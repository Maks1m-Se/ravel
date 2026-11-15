"""Session state for the table builder; generation rules live in the engine."""

from copy import deepcopy
import csv
from io import StringIO
import re

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
        self.selected = candidate["table"]["fields"][-1]["id"]
        self.result = None
        self.saved_recipe_json = dumps(candidate) if saved else None
        self.exported_result = None
        self.discard()

    @property
    def field(self):
        return next(f for f in self.recipe["table"]["fields"] if f["id"] == self.selected)

    def table_form(self):
        form = dict(name=self.recipe["table"]["name"], row_count=str(self.recipe["table"]["row_count"]),
                    seed=str(self.recipe["seed"]))
        if "sample" in self.recipe:
            form["mode"] = self.recipe["sample"]["mode"]
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

    def mark_exported(self):
        if self.current:
            self.exported_result = self.result

    def require_applied(self):
        if self.has_drafts:
            raise ValidationError("drafts", "Apply or discard unapplied edits first.")

    def apply(self):
        candidate = deepcopy(self.recipe)
        candidate["seed"] = whole(self.table_draft["seed"], "seed")
        candidate["table"]["name"] = self.table_draft["name"].strip()
        candidate["table"]["row_count"] = whole(self.table_draft["row_count"], "table.row_count")
        index = next(i for i, f in enumerate(candidate["table"]["fields"]) if f["id"] == self.selected)
        candidate["table"]["fields"][index] = form_field(self.field_draft, f"table.fields.{index}")
        if self.field_draft["kind"] in {"normal","boolean","date","date_sequence","category_quota"} or "unique" in self.field_draft:
            candidate["format"] = "ravel-single-table/3"
        elif self.field_draft["kind"] == "text_id" and candidate["format"]=="ravel-single-table/1":
            candidate["format"] = "ravel-single-table/2"
        if "sample" in candidate:
            candidate["sample"]["mode"] = self.table_draft["mode"]
            if candidate["table"]["fields"][index] != self.field and self.selected in candidate["sample"]["confirmed"]:
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
        if not any(f["id"] == identity for f in self.recipe["table"]["fields"]):
            raise ValidationError("column", "Column no longer exists.")
        self.selected = identity
        self.discard()

    def add(self):
        self.require_applied()
        candidate = deepcopy(self.recipe)
        field = new_field(existing=candidate["table"]["fields"])
        candidate["table"]["fields"].append(field)
        self.recipe = validate(candidate)
        self.selected = field["id"]
        self.discard()

    def duplicate(self):
        self.require_applied()
        candidate = deepcopy(self.recipe)
        duplicate = duplicate_field(self.field, candidate["table"]["fields"])
        candidate["table"]["fields"].append(duplicate)
        self.recipe = validate(candidate)
        self.selected = duplicate["id"]
        self.discard()

    def remove(self):
        self.require_applied()
        candidate = deepcopy(self.recipe)
        candidate["table"]["fields"] = [f for f in candidate["table"]["fields"] if f["id"] != self.selected]
        if "sample" in candidate:
            for key in ("identifiers", "confirmed"):
                candidate["sample"][key] = [value for value in candidate["sample"][key] if value != self.selected]
        self.recipe = validate(candidate)
        self.selected = self.recipe["table"]["fields"][-1]["id"]
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
        return csv_text(self.result)
