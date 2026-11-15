"""Session state for the table builder; generation rules live in the engine."""

from copy import deepcopy
import csv
from io import StringIO
import re
import json
from uuid import uuid4

from .engine import csv_text
from .recipe import PARAMETERS, ValidationError, dumps, duplicate_field, new_field, new_recipe, validate


def field_form(field):
    form = {key: str(value) for key, value in field.items() if key not in {"values", "probabilities"}}
    if field["kind"] in {"category", "category_quota"}:
        output = StringIO(newline="")
        csv.writer(output, lineterminator="\n").writerows(zip(field["values"], field["probabilities" if field["kind"]=="category" else "counts"]))
        form["categories" if field["kind"]=="category" else "quotas"] = output.getvalue().rstrip("\n")
        form.pop('counts', None)
    return form


def whole(value, path):
    if not isinstance(value, str) or not re.fullmatch(r"[+-]?\d{1,20}", value.strip()):
        raise ValidationError(path, "Enter a whole number.")
    return int(value)


def form_field(form, path):
    kind = form["kind"]
    field = {key: form[key] for key in ("id", "name", "kind", "missing_probability")}
    if "unique" in form:
        field["unique"] = form["unique"] == "True"
    field["name"] = field["name"].strip()
    for key in PARAMETERS[kind]:
        if key in {"values", "probabilities", "counts"}:
            continue
        value = form[key]
        if (key in {"start", "step", "places", "width", "missing_count"} and not (kind=="date_sequence" and key=="start")) or kind == "integer":
            value = whole(value, path + "." + key)
        field[key] = value
    if kind in {"category", "category_quota"}:
        try:
            rows = list(csv.reader(StringIO(form["categories" if kind=="category" else "quotas"]), strict=True))
        except csv.Error as exc:
            raise ValidationError(path + ".categories", "Use CSV lines: category,probability.") from exc
        if not rows or any(len(row) != 2 for row in rows):
            raise ValidationError(path + ".categories", "Use one category,probability pair per CSV line.")
        field["values"] = [row[0] for row in rows]
        field["probabilities" if kind=="category" else "counts"] = [row[1].strip() if kind=="category" else whole(row[1],path+'.counts') for row in rows]
    return field


class Workspace:
    def __init__(self, recipe=None):
        self.result = None
        self.replace(new_recipe() if recipe is None else recipe)

    def replace(self, recipe, saved=True):
        candidate = validate(recipe)
        self.recipe = candidate
        self.table_id = candidate['tables'][0]['id'] if 'tables' in candidate else candidate['table']['id']
        self.selected = self.table["fields"][-1]["id"]
        self.table_selection = {}
        self.result = None
        self.saved_recipe_json = dumps(candidate) if saved else None
        self.exported_result = None
        self.exported_tables = set()
        self.export_tracking_result = None
        self.discard()

    @property
    def is_dataset(self):
        return 'tables' in self.recipe

    def _table(self,document):
        return next(table for table in document['tables'] if table['id']==self.table_id) if 'tables' in document else document['table']

    @property
    def table(self):
        return self._table(self.recipe)

    @property
    def table_result(self):
        from .dataset import DatasetResult
        if isinstance(self.result,DatasetResult):
            return self.result.table(self.table_id)
        if self.result is not None and self.is_dataset and json.loads(self.result.recipe_json).get('table',{}).get('id')!=self.table_id:
            return None
        return self.result

    @property
    def field(self):
        return next(f for f in self.table["fields"] if f["id"] == self.selected)

    def table_form(self):
        form = dict(name=self.table["name"], row_count=str(self.table["row_count"]),
                    seed=str(self.recipe["seed"]))
        if "sample" in self.recipe:
            form["mode"] = self.recipe["sample"]["mode"]
        if self.is_dataset:
            form['primary_key']=self.table['primary_key'] or ''
        return form

    def discard(self):
        self.field_draft = field_form(self.field)
        self.table_draft = self.table_form()

    @property
    def has_drafts(self):
        return self.field_draft != field_form(self.field) or self.table_draft != self.table_form()

    @property
    def current(self):
        return self.result is not None and not self.has_drafts and self.result.recipe_json == dumps(self.recipe)

    @property
    def has_unsaved(self):
        return self.has_drafts or dumps(self.recipe) != self.saved_recipe_json or (self.result is not None and self.result is not self.exported_result)

    def mark_saved(self):
        self.require_applied()
        self.saved_recipe_json = dumps(self.recipe)

    def mark_exported(self,all_tables=False):
        if self.current:
            if not self.is_dataset:
                self.exported_result = self.result
            else:
                if self.export_tracking_result is not self.result:
                    self.exported_tables=set()
                    self.export_tracking_result=self.result
                self.exported_tables.add(self.table_id)
                if all_tables or self.exported_tables=={table['id'] for table in self.recipe['tables']}:
                    self.exported_result=self.result

    def require_applied(self):
        if self.has_drafts:
            raise ValidationError("drafts", "Apply or discard unapplied edits first.")

    def apply(self):
        candidate = deepcopy(self.recipe)
        candidate["seed"] = whole(self.table_draft["seed"], "seed")
        table=self._table(candidate)
        table["name"] = self.table_draft["name"].strip()
        table["row_count"] = whole(self.table_draft["row_count"], "table.row_count")
        index = next(i for i, f in enumerate(table["fields"]) if f["id"] == self.selected)
        table["fields"][index] = form_field(self.field_draft, f"table.fields.{index}")
        if self.is_dataset:
            table['primary_key']=self.table_draft['primary_key'] or None
        elif self.field_draft["kind"] in {"normal","boolean","date","date_sequence","category_quota"} or "unique" in self.field_draft:
            candidate["format"] = "ravel-single-table/3"
        elif self.field_draft["kind"] == "text_id" and candidate["format"]=="ravel-single-table/1":
            candidate["format"] = "ravel-single-table/2"
        if "sample" in candidate:
            candidate["sample"]["mode"] = self.table_draft["mode"]
            if table["fields"][index] != self.field and self.selected in candidate["sample"]["confirmed"]:
                candidate["sample"]["confirmed"].remove(self.selected)
        self.recipe = validate(candidate)
        self.discard()

    def change_kind(self, kind):
        defaults = field_form(new_field(kind))
        for key in ("id", "name", "missing_probability"):
            defaults[key] = self.field_draft[key]
        self.field_draft = defaults

    def select(self, identity):
        self.require_applied()
        if not any(f["id"] == identity for f in self.table["fields"]):
            raise ValidationError("column", "Column no longer exists.")
        self.selected = identity
        self.discard()

    def add(self):
        self.require_applied()
        candidate = deepcopy(self.recipe)
        field = new_field(existing=self._table(candidate)["fields"])
        self._table(candidate)["fields"].append(field)
        self.recipe = validate(candidate)
        self.selected = field["id"]
        self.discard()

    def duplicate(self):
        self.require_applied()
        candidate = deepcopy(self.recipe)
        if self.field['kind'] in {'foreign_key','child_index'}:
            raise ValidationError('column','Relationship columns cannot be duplicated; add an ordinary column instead.')
        duplicate = duplicate_field(self.field, self._table(candidate)["fields"])
        self._table(candidate)["fields"].append(duplicate)
        self.recipe = validate(candidate)
        self.selected = duplicate["id"]
        self.discard()

    def remove(self):
        self.require_applied()
        candidate = deepcopy(self.recipe)
        self._table(candidate)["fields"] = [f for f in self._table(candidate)["fields"] if f["id"] != self.selected]
        if "sample" in candidate:
            for key in ("identifiers", "confirmed"):
                candidate["sample"][key] = [value for value in candidate["sample"][key] if value != self.selected]
        self.recipe = validate(candidate)
        self.selected = self.table["fields"][-1]["id"]
        self.discard()

    def confirm_identifier(self):
        self.require_applied()
        if self.selected not in self.recipe.get("sample", {}).get("identifiers", []):
            raise ValidationError("sample.identifiers", "Select a source identifier first.")
        if self.field["kind"] not in {"id", "text_id"}:
            raise ValidationError("sample.identifiers", "Choose and apply a sequential ID or formatted ID rule first.")
        candidate = deepcopy(self.recipe)
        if self.selected not in candidate["sample"]["confirmed"]:
            candidate["sample"]["confirmed"].append(self.selected)
        self.recipe = validate(candidate)

    def recipe_for_run(self):
        self.require_applied()
        return validate(self.recipe)

    def save_recipe(self):
        self.require_applied()
        return dumps(self.recipe)

    def export_csv(self):
        if not self.current:
            raise ValidationError("result", "Generate a current result after applying or discarding edits before export.")
        if self.table_result is None:
            raise ValidationError('result','Generate the complete dataset before exporting this table.')
        return csv_text(self.table_result)

    def select_table(self,identity):
        self.require_applied()
        if not self.is_dataset or identity not in {table['id'] for table in self.recipe['tables']}:
            raise ValidationError('table','Table no longer exists.')
        self.table_selection[self.table_id]=self.selected
        self.table_id=identity
        self.selected=self.table_selection.get(identity,self.table['fields'][-1]['id'])
        if self.selected not in {field['id'] for field in self.table['fields']}:
            self.selected=self.table['fields'][-1]['id']
        self.discard()

    def add_table(self):
        self.require_applied()
        if 'sample' in self.recipe:
            raise ValidationError('table','Joined sample fitting is not supported; save this sample recipe and start a linked template separately.')
        if self.is_dataset:
            candidate=deepcopy(self.recipe)
        else:
            old=deepcopy(self.table)
            old['primary_key']=next((field['id'] for field in old['fields'] if field['kind'] in {'id','text_id'}),None)
            candidate=dict(format='ravel-dataset/1',seed=self.recipe['seed'],tables=[old],relationships=[])
        table=new_recipe()['table']
        stem=f'Table {len(candidate["tables"])+1}'
        table.update(id='t_'+uuid4().hex,name=stem,primary_key='row_id')
        used={item['name'] for item in candidate['tables']}
        number=2
        while table['name'] in used:
            table['name']=f'{stem} ({number})'
            number+=1
        candidate['tables'].append(table)
        self.recipe=validate(candidate)
        self.table_selection[self.table_id]=self.selected
        self.table_id=table['id']
        self.selected=table['fields'][-1]['id']
        self.discard()

    def relationship_candidate(self,parent_id,per):
        self.require_applied()
        from .recipe import integer
        integer(per,'relationships.children_per_parent',1,100000)
        if not self.is_dataset:
            raise ValidationError('relationships','Add a second table first.')
        candidate=deepcopy(self.recipe)
        child=self._table(candidate)
        parent=next((table for table in candidate['tables'] if table['id']==parent_id),None)
        if parent is None or parent['primary_key'] is None:
            raise ValidationError('relationships','Choose a parent with an explicit primary key.')
        link=next((link for link in candidate['relationships'] if link['child']==self.table_id),None)
        if link is None:
            foreign=new_field('foreign_key',child['fields'])
            stem=next(field['name'] for field in parent['fields'] if field['id']==parent['primary_key'])
            foreign['name']=stem
            used={field['name'] for field in child['fields']}
            number=1
            while foreign['name'] in used:
                foreign['name']=stem[:32]+f'_ref{number}'
                number+=1
            child['fields'].append(foreign)
            used.add(foreign['name'])
            slot=new_field('child_index',child['fields'])
            slot['name']='slot' if 'slot' not in used else slot['name']
            child['fields'].append(slot)
            link=dict(id='rel_'+uuid4().hex,parent=parent_id,parent_key=parent['primary_key'],child=self.table_id,foreign_key=foreign['id'],children_per_parent=per)
            candidate['relationships'].append(link)
        else:
            link.update(parent=parent_id,parent_key=parent['primary_key'],children_per_parent=per)
        from .dataset import topology
        tables={table['id']:table for table in candidate['tables']}
        for identity in topology(candidate):
            relation=next((item for item in candidate['relationships'] if item['child']==identity),None)
            if relation:
                tables[identity]['row_count']=tables[relation['parent']]['row_count']*relation['children_per_parent']
        return validate(candidate)

    def set_relationship(self,parent_id,per):
        self.recipe=self.relationship_candidate(parent_id,per)
        self.discard()

    def remove_relationship(self):
        self.require_applied()
        if not self.is_dataset:
            raise ValidationError('relationships','This table has no dataset relationship.')
        candidate=deepcopy(self.recipe)
        candidate['relationships']=[link for link in candidate['relationships'] if link['child']!=self.table_id]
        self._table(candidate)['fields']=[field for field in self._table(candidate)['fields'] if field['kind'] not in {'foreign_key','child_index'}]
        self.recipe=validate(candidate)
        self.selected=self.table['fields'][-1]['id']
        self.discard()

    def export_dataset(self):
        from .dataset import DatasetResult,zip_bytes
        if not self.current or not isinstance(self.result,DatasetResult):
            raise ValidationError('result','Generate a current complete dataset before export.')
        return zip_bytes(self.result)
