"""Session state for the table builder; generation rules live in the engine."""

from copy import deepcopy
import csv
from io import StringIO
import re

from .engine import csv_text
from .recipe import PARAMETERS, ValidationError, dumps, duplicate_field, new_field, new_recipe, validate


def field_form(field):
    form = {key: str(value) for key, value in field.items() if key not in {"values", "probabilities"}}
    if field["kind"] == "category":
        output = StringIO(newline="")
        csv.writer(output, lineterminator="\n").writerows(zip(field["values"], field["probabilities"]))
        form["categories"] = output.getvalue().rstrip("\n")
    return form


def whole(value, path):
    if not isinstance(value, str) or not re.fullmatch(r"[+-]?\d{1,20}", value.strip()):
        raise ValidationError(path, "Enter a whole number.")
    return int(value)


def form_field(form, path):
    kind = form["kind"]
    field = {key: form[key] for key in ("id", "name", "kind", "missing_probability")}
    field["name"] = field["name"].strip()
    for key in PARAMETERS[kind]:
        if key in {"values", "probabilities"}:
            continue
        value = form[key]
        if key in {"start", "step", "places"} or kind == "integer":
            value = whole(value, path + "." + key)
        field[key] = value
    if kind == "category":
        try:
            rows = list(csv.reader(StringIO(form["categories"]), strict=True))
        except csv.Error as exc:
            raise ValidationError(path + ".categories", "Use CSV lines: category,probability.") from exc
        if not rows or any(len(row) != 2 for row in rows):
            raise ValidationError(path + ".categories", "Use one category,probability pair per CSV line.")
        field["values"] = [row[0] for row in rows]
        field["probabilities"] = [row[1].strip() for row in rows]
    return field


class Workspace:
    def __init__(self, recipe=None):
        self.result = None
        self.replace(new_recipe() if recipe is None else recipe)

    def replace(self, recipe):
        candidate = validate(recipe)
        self.recipe = candidate
        self.selected = candidate["table"]["fields"][-1]["id"]
        self.result = None
        self.discard()

    @property
    def field(self):
        return next(f for f in self.recipe["table"]["fields"] if f["id"] == self.selected)

    def table_form(self):
        return dict(name=self.recipe["table"]["name"], row_count=str(self.recipe["table"]["row_count"]),
                    seed=str(self.recipe["seed"]))

    def discard(self):
        self.field_draft = field_form(self.field)
        self.table_draft = self.table_form()

    @property
    def has_drafts(self):
        return self.field_draft != field_form(self.field) or self.table_draft != self.table_form()

    @property
    def current(self):
        return self.result is not None and not self.has_drafts and self.result.recipe_json == dumps(self.recipe)

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
        self.recipe = validate(candidate)
        self.selected = self.recipe["table"]["fields"][-1]["id"]
        self.discard()

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
