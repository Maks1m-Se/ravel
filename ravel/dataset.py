"""Bounded generic linked datasets and complete staged export."""

from collections import deque
from copy import deepcopy
from dataclasses import dataclass
from decimal import Decimal
from hashlib import sha256
from io import BytesIO
import json
from pathlib import Path
import shutil
import tempfile
import zipfile

from . import recipe as rules

FORMAT='ravel-dataset/1'
STRUCTURAL={'foreign_key','child_index'}


@dataclass(frozen=True)
class DatasetResult:
    recipe_json: str
    tables: tuple
    environment: tuple

    def table(self, identity):
        return dict(self.tables).get(identity)


def scalar_recipe(document,table):
    projected=dict(format='ravel-single-table/3',seed=document['seed'],table=deepcopy(table))
    projected['table'].pop('primary_key',None)
    for i,field in enumerate(table['fields']):
        if field.get('kind') in ('foreign_key','child_index'):
            projected['table']['fields'][i]=dict(id=field['id'],name=field['name'],kind='constant',value='derived',missing_probability='0')
    return projected


def topology(document):
    ids=[table['id'] for table in document['tables']]
    degree=dict.fromkeys(ids,0)
    for link in document['relationships']:
        degree[link['child']]+=1
    queue=deque(identity for identity in ids if degree[identity]==0)
    order=[]
    while queue:
        identity=queue.popleft()
        order.append(identity)
        for link in document['relationships']:
            if link['parent']==identity:
                degree[link['child']]-=1
                if not degree[link['child']]:
                    queue.append(link['child'])
    if len(order)!=len(ids):
        rules.fail('relationships','Relationships must be acyclic; remove the parent-child cycle.')
    return order


def validate(document):
    rules.keys(document,{'format','seed','tables','relationships'},'recipe')
    rules.integer(document['seed'],'seed',0,2**63-1)
    tables=document['tables']
    if not isinstance(tables,list) or not 1<=len(tables)<=8:
        rules.fail('tables','Use 1–8 tables.')
    by_id={}
    names=set()
    for i,table in enumerate(tables):
        path=f'tables.{i}'
        rules.keys(table,{'id','name','row_count','fields','primary_key'},path)
        rules.identity(table['id'],path+'.id')
        rules.name(table['name'],path+'.name')
        if table['id'] in by_id or table['name'] in names:
            rules.fail(path,'Table identities and names must be distinct.')
        by_id[table['id']]=table
        names.add(table['name'])
        if not isinstance(table['fields'],list):
            rules.fail(path+'.fields','Expected a list of columns.')
        for j,field in enumerate(table['fields']):
            if not isinstance(field,dict):
                rules.fail(f'{path}.fields.{j}','Expected a column object.')
            if field.get('kind') in ('foreign_key','child_index'):
                rules.keys(field,{'id','name','kind','missing_probability'},f'{path}.fields.{j}')
                if rules.decimal(field['missing_probability'],f'{path}.fields.{j}.missing_probability',0,1):
                    rules.fail(f'{path}.fields.{j}.missing_probability','Relationship columns cannot be missing.')
        try:
            rules.validate(scalar_recipe(document,table))
        except rules.ValidationError as exc:
            raise rules.ValidationError(path+'.'+exc.path.removeprefix('table.'),exc.message) from exc
        key=table['primary_key']
        if key is not None:
            rules.identity(key,path+'.primary_key')
            field=next((field for field in table['fields'] if field['id']==key),None)
            if field is None:
                rules.fail(path+'.primary_key','Primary key column does not exist.')
            if field['kind']=='constant' and table['row_count']>1:
                rules.fail(path+'.primary_key','Primary key would contain duplicate constant values.')
            if not (field['kind'] in {'id','text_id'} or field.get('unique') or
                    (field['kind']=='constant' and table['row_count']==1)) or Decimal(field['missing_probability']):
                rules.fail(path+'.primary_key','Choose a nonmissing ID or declared finite-domain unique column for the primary key.')
    if sum(table['row_count']*len(table['fields']) for table in tables)>2_000_000:
        rules.fail('tables','The complete dataset supports at most 2,000,000 cells.')
    links=document['relationships']
    if not isinstance(links,list) or len(links)>7:
        rules.fail('relationships','Use at most seven relationships.')
    link_ids,children,foreign_fields=set(),set(),set()
    for i,link in enumerate(links):
        path=f'relationships.{i}'
        rules.keys(link,{'id','parent','parent_key','child','foreign_key','children_per_parent'},path)
        for key in ['id','parent','parent_key','child','foreign_key']:
            rules.identity(link[key],path+'.'+key)
        rules.integer(link['children_per_parent'],path+'.children_per_parent',1,100000)
        if link['id'] in link_ids or link['child'] in children:
            rules.fail(path,'Relationship identities must be distinct and a child can have only one parent.')
        link_ids.add(link['id'])
        children.add(link['child'])
        if link['parent'] not in by_id or link['child'] not in by_id:
            rules.fail(path,'Parent and child must reference existing tables.')
        parent,child=by_id[link['parent']],by_id[link['child']]
        if parent['primary_key']!=link['parent_key']:
            rules.fail(path+'.parent_key','Reference the parent table’s declared primary key.')
        foreign=next((field for field in child['fields'] if field['id']==link['foreign_key']),None)
        if foreign is None or foreign['kind']!='foreign_key':
            rules.fail(path+'.foreign_key','Choose an existing Parent key column in the child table.')
        foreign_fields.add((child['id'],foreign['id']))
    topology(document)
    for i,table in enumerate(tables):
        for field in table['fields']:
            if field['kind']=='foreign_key' and (table['id'],field['id']) not in foreign_fields:
                rules.fail(f'tables.{i}.fields','Parent key column has no relationship.')
            if field['kind']=='child_index' and table['id'] not in children:
                rules.fail(f'tables.{i}.fields','Child index requires a parent relationship.')
    for link in links:
        parent,child=by_id[link['parent']],by_id[link['child']]
        expected=parent['row_count']*link['children_per_parent']
        if child['row_count']!=expected:
            rules.fail(f'tables.{tables.index(child)}.row_count',f'{child["name"]} declares {child["row_count"]:,} rows; its relationship requires {expected:,} ({parent["row_count"]:,} × {link["children_per_parent"]:,}).')
    if len(rules._canonical_json(document).encode('utf-8'))>rules.MAX_BYTES:
        rules.fail('recipe','The complete saved recipe must fit within 1 MiB.')
    return deepcopy(document)


def generate(document):
    from .engine import Result,generate as scalar_generate,environment
    candidate=validate(document)
    canonical=rules.dumps(candidate)
    tables={table['id']:table for table in candidate['tables']}
    results={}
    for identity in topology(candidate):
        table=tables[identity]
        scalar=scalar_generate(scalar_recipe(candidate,table))
        rows=[list(row) for row in scalar.rows]
        link=next((link for link in candidate['relationships'] if link['child']==identity),None)
        if link:
            parent=tables[link['parent']]
            key_index=next(i for i,field in enumerate(parent['fields']) if field['id']==link['parent_key'])
            keys=[row[key_index] for row in results[parent['id']].rows]
            per=link['children_per_parent']
            for i,field in enumerate(table['fields']):
                if field['kind'] in STRUCTURAL:
                    for j,row in enumerate(rows):
                        row[i]=keys[j//per] if field['kind']=='foreign_key' else j%per+1
            foreign_index=next(i for i,field in enumerate(table['fields']) if field['id']==link['foreign_key'])
            parent_keys=set(keys)
            if any(row[foreign_index] not in parent_keys for row in rows):
                rules.fail('result','Foreign-key validation failed; no successful dataset produced.')
        if table['primary_key']:
            index=next(i for i,field in enumerate(table['fields']) if field['id']==table['primary_key'])
            keys=[row[index] for row in rows]
            if None in keys or len(set(keys))!=len(keys):
                rules.fail('result',f'{table["name"]} contains missing or duplicate primary keys.')
        results[identity]=Result(canonical,scalar.headers,tuple(tuple(row) for row in rows),environment())
    return DatasetResult(canonical,tuple((table['id'],results[table['id']]) for table in candidate['tables']),environment())


def run_metadata(result):
    from .engine import csv_text
    document=json.loads(result.recipe_json)
    return dict(format='ravel-dataset-run/1',environment=dict(result.environment),
        recipe_sha256=sha256(result.recipe_json.encode()).hexdigest(),
        tables={identity:dict(row_count=len(table.rows),column_count=len(table.headers),csv_sha256=sha256(csv_text(table).encode()).hexdigest()) for identity,table in result.tables},
        validation=dict(status='passed',checks=['table counts','primary keys','foreign keys','acyclic relationships']),
        relationships=document['relationships'])


def payloads(result):
    from .engine import csv_text
    document=json.loads(result.recipe_json)
    dictionary=dict(format='ravel-dictionary/1',tables=[dict(id=table['id'],name=table['name'],primary_key=table['primary_key'],columns=table['fields']) for table in document['tables']])
    files={identity+'.csv':csv_text(table).encode('utf-8') for identity,table in result.tables}
    files['recipe.json']=result.recipe_json.encode('utf-8')
    files['dictionary.json']=(json.dumps(dictionary,ensure_ascii=False,indent=2)+'\n').encode('utf-8')
    files['run.json']=(json.dumps(run_metadata(result),ensure_ascii=False,indent=2)+'\n').encode('utf-8')
    return files


def zip_bytes(result):
    output=BytesIO()
    with zipfile.ZipFile(output,'w',compression=zipfile.ZIP_DEFLATED) as archive:
        for name,content in payloads(result).items():
            entry=zipfile.ZipInfo(name,date_time=(1980,1,1,0,0,0))
            entry.compress_type=zipfile.ZIP_DEFLATED
            archive.writestr(entry,content)
    return output.getvalue()


def write_outputs(destination,result):
    destination=Path(destination).resolve()
    if destination.exists():
        raise FileExistsError(f'Output already exists: {destination}. Choose a new dataset directory.')
    files=payloads(result)
    parent=destination.parent
    staged=Path(tempfile.mkdtemp(prefix='.'+destination.name+'-staging-',dir=parent)).resolve()
    assert staged.parent==parent and staged.name.startswith('.'+destination.name+'-staging-')
    try:
        for name,content in files.items():
            (staged/name).write_bytes(content)
        if destination.exists():
            raise FileExistsError('Dataset destination appeared during staging; no existing output was overwritten.')
        staged.rename(destination)
    finally:
        if staged.exists():
            assert staged.parent==parent and staged.name.startswith('.'+destination.name+'-staging-')
            shutil.rmtree(staged)
    return [destination/name for name in files]


def template():
    return rules.loads((Path(__file__).resolve().parents[1]/'examples/linked/devices-measurements.recipe.json').read_bytes())
