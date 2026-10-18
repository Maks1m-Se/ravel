"""Versioned declarative recipes and shared validation."""

from copy import deepcopy
from decimal import Decimal
from fractions import Fraction
import json
import re
from uuid import uuid4

FORMAT = "ravel-single-table/1"
MAX_BYTES = 1_048_576
LIMIT = 10**12
KINDS = ("id", "constant", "sequence", "integer", "decimal", "category")
PARAMETERS = {
    "id": {"start"}, "constant": {"value"}, "sequence": {"start", "step"},
    "integer": {"minimum", "maximum"}, "decimal": {"minimum", "maximum", "places"},
    "category": {"values", "probabilities"},
    "text_id": {"start", "prefix", "width"},
}


class ValidationError(ValueError):
    def __init__(self, path, message):
        self.path, self.message = path, message
        super().__init__(f"{path}: {message}")


def fail(path, message):
    raise ValidationError(path, message)


def keys(value, expected, path):
    if not isinstance(value, dict):
        fail(path, "Expected an object.")
    if set(value) != expected:
        missing, extra = expected - set(value), set(value) - expected
        detail = []
        if missing:
            detail.append("Missing " + ", ".join(sorted(missing)))
        if extra:
            detail.append("Unsupported " + ", ".join(sorted(map(str, extra))))
        fail(path, "; ".join(detail) + ".")


def integer(value, path, low=-LIMIT, high=LIMIT):
    if type(value) is not int or not low <= value <= high:
        fail(path, f"Use a whole number from {low:,} to {high:,}.")
    return value


def decimal(value, path, low=-LIMIT, high=LIMIT, places=12):
    if not isinstance(value, str) or len(value) > 40 or not re.fullmatch(r"-?\d+(?:\.\d+)?", value):
        fail(path, "Use plain decimal text, for example 0.25 (no exponent).")
    number = Decimal(value)
    if not low <= number <= high or -number.as_tuple().exponent > places:
        fail(path, f"Use a value from {low} to {high} with at most {places} decimal places.")
    return number


def text(value, path, maximum=200):
    if not isinstance(value, str) or not value or len(value) > maximum or "\x00" in value:
        fail(path, f"Use nonempty text up to {maximum} characters, without NUL.")
    try:
        value.encode("utf-8")
    except UnicodeEncodeError:
        fail(path, "Use valid Unicode text.")
    return value


def name(value, path):
    text(value, path, 40)
    if value != value.strip() or any(ord(c) < 32 for c in value):
        fail(path, "Names must be trimmed text without control characters.")


def identity(value, path):
    if not isinstance(value, str) or not re.fullmatch(r"[A-Za-z][A-Za-z0-9_-]{0,63}", value):
        fail(path, "Use a stable ID starting with a letter, then letters, digits, _ or - (up to 64).")


def _canonical_json(recipe):
    return json.dumps(recipe, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False) + "\n"


def validate(recipe):
    if isinstance(recipe, dict) and recipe.get("format") == "ravel-single-table/2":
        from .sample import validate as validate_sample
        return validate_sample(recipe)
    if isinstance(recipe, dict) and recipe.get("format") == "ravel-workbook-experiment/1":
        fail("format", "Old workbook experiment JSON is not a generation recipe. Keep the original; recreate its rules explicitly in Ravel. No migration was performed.")
    if not isinstance(recipe, dict) or recipe.get("format") != FORMAT:
        fail("format", f"Supported format is {FORMAT}; supplied {recipe.get('format') if isinstance(recipe, dict) else type(recipe).__name__!r}.")
    keys(recipe, {"format", "seed", "table"}, "recipe")
    integer(recipe["seed"], "seed", 0, 2**63 - 1)
    table = recipe["table"]
    keys(table, {"id", "name", "row_count", "fields"}, "table")
    identity(table["id"], "table.id")
    name(table["name"], "table.name")
    count = integer(table["row_count"], "table.row_count", 1, 100_000)
    fields = table["fields"]
    if not isinstance(fields, list) or not 1 <= len(fields) <= 50:
        fail("table.fields", "Use between 1 and 50 columns.")
    if count * len(fields) > 2_000_000:
        fail("table.row_count", "This increment supports at most 2,000,000 cells; reduce rows or columns.")
    ids, names = set(), set()
    for index, field in enumerate(fields):
        path = f"table.fields.{index}"
        kind = field.get("kind") if isinstance(field, dict) else None
        if not isinstance(kind, str) or kind not in KINDS:
            fail(path + ".kind", "Choose a supported rule: " + ", ".join(KINDS) + ".")
        keys(field, {"id", "name", "kind", "missing_probability"} | PARAMETERS[kind], path)
        identity(field["id"], path + ".id")
        name(field["name"], path + ".name")
        if field["id"] in ids:
            fail(path + ".id", "Column identities must be unique; duplication needs a new ID.")
        if field["name"] in names:
            fail(path + ".name", "Column names must be unique.")
        ids.add(field["id"])
        names.add(field["name"])
        missing = decimal(field["missing_probability"], path + ".missing_probability", 0, 1)
        if kind in {"id", "sequence"}:
            start = integer(field["start"], path + ".start", 1 if kind == "id" else -LIMIT)
            step = 1 if kind == "id" else integer(field["step"], path + ".step")
            integer(start + (count - 1) * step, path + ".start", 1 if kind == "id" else -LIMIT)
            if kind == "id" and missing:
                fail(path + ".missing_probability", "Sequential identifiers cannot be missing.")
        elif kind == "constant":
            text(field["value"], path + ".value")
        elif kind in {"integer", "decimal"}:
            if kind == "integer":
                low = integer(field["minimum"], path + ".minimum")
                high = integer(field["maximum"], path + ".maximum")
            else:
                places = integer(field["places"], path + ".places", 0, 6)
                low = decimal(field["minimum"], path + ".minimum", places=places)
                high = decimal(field["maximum"], path + ".maximum", places=places)
            if low > high:
                fail(path + ".minimum", "Minimum must not exceed maximum.")
        else:
            values, probabilities = field["values"], field["probabilities"]
            if not isinstance(values, list) or not 1 <= len(values) <= 100:
                fail(path + ".values", "Use between 1 and 100 distinct categories.")
            for value in values:
                text(value, path + ".values")
            if len(set(values)) != len(values):
                fail(path + ".values", "Category values must be distinct.")
            if not isinstance(probabilities, list) or len(probabilities) != len(values):
                fail(path + ".probabilities", "Provide one probability for every category.")
            weights = [decimal(p, path + ".probabilities", 0, 1) for p in probabilities]
            if sum(Fraction(weight) for weight in weights) != 1:
                fail(path + ".probabilities", "Category probabilities must sum exactly to 1.")
    if len(_canonical_json(recipe).encode("utf-8")) > MAX_BYTES:
        fail("recipe", "Recipe must fit within 1 MiB when saved; reduce columns, categories or text length.")
    return deepcopy(recipe)


def dumps(recipe):
    return _canonical_json(validate(recipe))


def loads(payload):
    if isinstance(payload, str):
        try:
            payload = payload.encode("utf-8")
        except UnicodeEncodeError:
            fail("recipe", "Recipe must contain valid UTF-8 text.")
    if not isinstance(payload, bytes) or len(payload) > MAX_BYTES:
        fail("recipe", "Recipe must be UTF-8 JSON no larger than 1 MiB.")

    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                fail("recipe", f"Duplicate JSON key: {key}.")
            result[key] = value
        return result

    try:
        parsed = json.loads(payload.decode("utf-8"), object_pairs_hook=pairs,
                            parse_constant=lambda value: fail("recipe", f"Unsupported JSON number {value}."))
    except (UnicodeDecodeError, json.JSONDecodeError, RecursionError) as exc:
        fail("recipe", "Read a valid UTF-8 JSON recipe. " + str(exc))
    return validate(parsed)


def new_field(kind="integer", existing=()):
    defaults = {
        "id": {"start": 1}, "constant": {"value": "demo"},
        "sequence": {"start": 10, "step": 2}, "integer": {"minimum": 0, "maximum": 100},
        "decimal": {"minimum": "0.00", "maximum": "100.00", "places": 2},
        "category": {"values": ["A", "B"], "probabilities": ["0.5", "0.5"]},
        "text_id": {"start": 1, "prefix": "", "width": 3},
    }
    used = {f["name"] for f in existing}
    stem, candidate, index = "column", "column", 2
    while candidate in used:
        candidate, index = f"{stem}_{index}", index + 1
    return dict(id="f_" + uuid4().hex, name=candidate, kind=kind,
                missing_probability="0", **defaults[kind])


def duplicate_field(field, existing):
    duplicate = deepcopy(field)
    duplicate["id"] = "f_" + uuid4().hex
    used = {f["name"] for f in existing}
    index = 1
    while True:
        suffix = "_copy" if index == 1 else f"_copy{index}"
        candidate = field["name"][:40 - len(suffix)] + suffix
        if candidate not in used:
            duplicate["name"] = candidate
            return duplicate
        index += 1


def new_recipe():
    fields = [dict(id="row_id", name="id", kind="id", start=1, missing_probability="0"),
              dict(id="value", name="value", kind="integer", minimum=0, maximum=100, missing_probability="0")]
    return dict(format=FORMAT, seed=17, table=dict(id="main", name="Untitled table", row_count=1000, fields=fields))
