"""Bounded CSV profiling and source composition; no UI or clinical semantics."""

from collections import Counter
from copy import deepcopy
import csv
from decimal import Decimal
from hashlib import sha256
from io import StringIO
import re

from . import recipe as rules

FORMAT = 'ravel-single-table/2'


def parse_csv(payload, delimiter=','):
    if not isinstance(delimiter, str) or delimiter not in {',', ';', '\t'}:
        rules.fail('sample.delimiter', 'Choose comma, semicolon or tab explicitly.')
    if isinstance(payload, str):
        try:
            payload = payload.encode('utf-8')
        except UnicodeEncodeError:
            rules.fail('sample', 'Use valid UTF-8 CSV text.')
    if not isinstance(payload, bytes) or len(payload) > rules.MAX_BYTES:
        rules.fail('sample', 'CSV must be UTF-8 and no larger than 1 MiB.')
    try:
        text = payload.decode('utf-8')
        rows = list(csv.reader(StringIO(text.removeprefix('\ufeff'), newline=''), delimiter=delimiter, strict=True))
    except (UnicodeError, csv.Error) as exc:
        rules.fail('sample', 'Read valid UTF-8 CSV records: ' + str(exc))
    if len(rows) < 2 or not 1 <= len(rows[0]) <= 49:
        rules.fail('sample', 'Provide a header and at least one data row, with 1–49 source columns.')
    headers = rows.pop(0)
    for header in headers:
        rules.name(header, 'sample.headers')
    if len(set(headers)) != len(headers):
        rules.fail('sample.headers', 'Source headers must be distinct.')
    if 'row_origin' in headers:
        rules.fail('sample.headers', 'row_origin is reserved for output provenance; rename that source header explicitly.')
    if len(rows) > 100_000:
        rules.fail('sample', 'Use at most 100,000 source rows.')
    for i, row in enumerate(rows, 2):
        if len(row) != len(headers):
            rules.fail(f'sample.row.{i}', f'Expected {len(headers)} cells; found {len(row)}.')
        for j, cell in enumerate(row, 1):
            if cell:
                rules.text(cell, f'sample.row.{i}.column.{j}')
    return text, headers, rows


def probability(numerator, denominator):
    ticks = (numerator * 10**12 + denominator // 2) // denominator
    return format(Decimal(ticks).scaleb(-12), 'f').rstrip('0').rstrip('.') or '0'


def infer(headers, rows):
    fields, identifiers = [], []
    for i, name in enumerate(headers):
        cells = [row[i] for row in rows]
        present = [cell for cell in cells if cell != '']
        field = dict(id=f'sample_{i}', name=name, missing_probability=probability(len(cells)-len(present), len(cells)))
        identifier = name.lower() == 'id' or name.lower().endswith('_id')
        if identifier:
            identifiers.append(field['id'])
            field['missing_probability'] = '0'
            if present and all(re.fullmatch(r'[1-9]\d*', s) for s in present):
                field.update(kind='id', start=max(map(int, present)) + 1)
            elif present and all(re.fullmatch(r'\d+', s) for s in present) and len({len(s) for s in present}) == 1:
                field.update(kind='text_id', prefix='', width=len(present[0]), start=max(map(int, present)) + 1)
            else:
                field.update(kind='constant', value='Choose an identifier rule')
        elif present and all(re.fullmatch(r'-?(?:0|[1-9]\d*)(?:\.\d+)?', s) for s in present):
            places = max(len(s.partition('.')[2]) for s in present)
            values = list(map(Decimal, present))
            if places:
                field.update(kind='decimal', minimum=format(min(values),'f'), maximum=format(max(values),'f'), places=places)
            else:
                field.update(kind='integer', minimum=int(min(values)), maximum=int(max(values)))
        elif not present:
            field.update(kind='constant', value='demo')
        else:
            counts = Counter(present)
            if len(counts) > 100:
                rules.fail(f'sample.column.{i+1}', 'More than 100 text categories; provide an explicit supported rule instead.')
            values = list(counts)
            weights = [counts[value] * 10**12 // len(present) for value in values]
            remainder = 10**12 - sum(weights)
            order = sorted(range(len(values)), key=lambda j: (-(counts[values[j]]*10**12 % len(present)), j))
            for j in order[:remainder]:
                weights[j] += 1
            field.update(kind='category', values=values, probabilities=[format(Decimal(w).scaleb(-12),'f') for w in weights])
        fields.append(field)
    return fields, identifiers


def profile(payload, delimiter=',', mode='new', count=1000, seed=17, confirm_identifiers=False):
    text, headers, rows = parse_csv(payload, delimiter)
    fields, identifiers = infer(headers, rows)
    document = dict(format=FORMAT, seed=seed, table=dict(id='main', name='Imported table', row_count=count, fields=fields),
        sample=dict(csv_utf8=text, sha256=sha256(text.encode('utf-8')).hexdigest(), delimiter=delimiter,
                    mode=mode, origin_column='row_origin', source_fields={f['id']:i for i,f in enumerate(fields)},
                    suggestions={f['id']:deepcopy(f) for f in fields}, identifiers=identifiers,
                    confirmed=identifiers[:] if confirm_identifiers else []))
    return validate(document)


def context(document):
    sample = document.get('sample')
    if sample is None:
        return None
    rules.keys(sample, {'csv_utf8','sha256','delimiter','mode','origin_column','source_fields','suggestions','identifiers','confirmed'}, 'sample')
    text, headers, rows = parse_csv(sample['csv_utf8'], sample['delimiter'])
    if sample['sha256'] != sha256(text.encode('utf-8')).hexdigest():
        rules.fail('sample.sha256', 'Source checksum mismatch; reload the matching original source.')
    if not isinstance(sample['mode'], str) or sample['mode'] not in {'new','extend'}:
        rules.fail('sample.mode', 'Choose Generate new rows or Extend to total.')
    if sample['origin_column'] != 'row_origin':
        rules.fail('sample.origin_column', 'This version uses the reserved row_origin output column.')
    inferred, _ = infer(headers, rows)
    if sample['source_fields'] != {f['id']:i for i,f in enumerate(inferred)} or sample['suggestions'] != {f['id']:f for f in inferred}:
        rules.fail('sample', 'Source binding or original suggestions do not match the recorded CSV.')
    current = {field['id'] for field in document['table']['fields'] if isinstance(field, dict) and 'id' in field}
    for key in ['identifiers','confirmed']:
        values = sample[key]
        if not isinstance(values, list) or any(not isinstance(value,str) for value in values) or len(set(values)) != len(values):
            rules.fail('sample.'+key, 'Provide distinct source field identities.')
    if not set(sample['identifiers']) <= (set(sample['source_fields']) & current) or not set(sample['confirmed']) <= set(sample['identifiers']):
        rules.fail('sample.identifiers', 'Identifier roles/confirmations must refer to present source fields.')
    if sample['mode'] == 'extend' and not set(sample['source_fields']) <= current:
        rules.fail('sample', 'Retain-and-extend must keep every source column; use generated-only to remove one.')
    target = document['table']['row_count']
    retained = len(rows) if sample['mode'] == 'extend' else 0
    if target < retained:
        rules.fail('table.row_count', f'Total must be at least the {retained} retained source rows; originals are never truncated.')
    return headers, rows, retained, target-retained


def validate(document):
    rules.keys(document, {'format','seed','table'} | ({'sample'} if 'sample' in document else set()), 'recipe')
    rules.keys(document['table'], {'id','name','row_count','fields'}, 'table')
    rules.integer(document['table']['row_count'], 'table.row_count', 1, 100_000)
    fields = document['table']['fields']
    if not isinstance(fields,list) or not 1 <= len(fields) <= 50:
        rules.fail('table.fields', 'Use between 1 and 50 columns.')
    for i, field in enumerate(fields):
        if not isinstance(field, dict):
            rules.fail(f'table.fields.{i}', 'Expected a column object.')
        rules.identity(field.get('id'), f'table.fields.{i}.id')
    source = context(document)
    count = source[3] if source else document['table']['row_count']
    projected = deepcopy(document)
    projected.pop('sample', None)
    projected['format'] = rules.FORMAT
    projected['table']['row_count'] = max(1,count)
    for i,field in enumerate(fields):
        if isinstance(field,dict) and field.get('kind') == 'text_id':
            path=f'table.fields.{i}'
            rules.keys(field, {'id','name','kind','missing_probability','prefix','width','start'},path)
            prefix=field['prefix']
            if not isinstance(prefix,str) or len(prefix)>40 or '\x00' in prefix:
                rules.fail(path+'.prefix','Use a text prefix up to 40 characters.')
            if prefix:
                rules.text(prefix,path+'.prefix',40)
            rules.integer(field['width'],path+'.width',1,20)
            rules.integer(field['start'],path+'.start',1)
            rules.integer(field['start']+max(0,count-1),path+'.start',1)
            if rules.decimal(field['missing_probability'],path+'.missing_probability',0,1):
                rules.fail(path+'.missing_probability','Identifiers cannot be missing.')
            projected['table']['fields'][i] = dict(id=field['id'],name=field['name'],kind='constant',value='id',missing_probability='0')
    rules.validate(projected)
    if source and (len(fields)+1 > 50 or document['table']['row_count']*(len(fields)+1)>2_000_000):
        rules.fail('table.row_count','Output including row origin supports at most 50 columns and 2,000,000 cells.')
    if source and any(field['name']=='row_origin' for field in fields):
        rules.fail('table.fields','row_origin is reserved for output provenance.')
    if len(rules._canonical_json(document).encode('utf-8')) > rules.MAX_BYTES:
        rules.fail('recipe','Recipe including its source must fit within 1 MiB when saved.')
    return deepcopy(document)


def compose(document, generator):
    from .engine import Result, environment
    headers, rows, retained, count = context(document)
    sample = document['sample']
    for field in document['table']['fields']:
        if count and field['id'] in sample['identifiers']:
            if field['id'] not in sample['confirmed'] or field['kind'] not in {'id','text_id'}:
                rules.fail('sample.identifiers', f'Confirm an explicit sequential identifier rule for {field["name"]}.')
            original = [row[sample['source_fields'][field['id']]] for row in rows]
            if '' in original or len(set(original)) != len(original):
                rules.fail('sample.identifiers', f'{field["name"]}: retained identifiers must be nonempty and unique.')
            new = [str(field['start']+i) if field['kind']=='id' else field['prefix']+str(field['start']+i).zfill(field['width']) for i in range(count)]
            if set(new) & set(original):
                rules.fail('sample.identifiers', f'{field["name"]}: generated identifiers collide with source identifiers; choose another start/prefix.')
    generated = ()
    if count:
        candidate=deepcopy(document)
        candidate.pop('sample')
        candidate['table']['row_count']=count
        generated=generator(candidate).rows
    fields=document['table']['fields']
    output = [tuple(row[sample['source_fields'][f['id']]] if f['id'] in sample['source_fields'] else None for f in fields)+('retained',) for row in rows[:retained]]
    output.extend(tuple(row)+('generated',) for row in generated)
    return Result(rules.dumps(document), tuple(f['name'] for f in fields)+('row_origin',), tuple(output), environment())


def assumption_origin(document, identity, key):
    original=document.get('sample',{}).get('suggestions',{}).get(identity)
    if original is None:
        return 'Explicit'
    field=next(f for f in document['table']['fields'] if f['id']==identity)
    if key=='categories':
        return 'Sample' if all(field.get(k)==original.get(k) for k in ['values','probabilities']) else 'Edited'
    return 'Sample' if field.get(key)==original.get(key) else 'Edited'
