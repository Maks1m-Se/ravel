"""Headless generator; no UI, filesystem or clinical rules."""

from bisect import bisect_right
import csv
from dataclasses import dataclass
from decimal import Decimal, localcontext
from hashlib import sha256
from io import StringIO
import json
import platform
from random import Random

from . import __version__
from .recipe import dumps, validate


@dataclass(frozen=True)
class Result:
    recipe_json: str
    headers: tuple[str, ...]
    rows: tuple[tuple[int | str | Decimal | None, ...], ...]
    environment: tuple[tuple[str, str], ...]


def _stream(seed, table_id, field_id, purpose):
    identity = json.dumps(["ravel-stream/1", seed, table_id, field_id, purpose], separators=(",", ":"))
    return Random(int.from_bytes(sha256(identity.encode()).digest(), "big"))


def _ratio(value):
    return Decimal(value).as_integer_ratio()


def generate(recipe):
    with localcontext() as context:
        context.prec = 40
        candidate = validate(recipe)
        if "sample" in candidate:
            from .sample import compose
            return compose(candidate, _generate)
        return _generate(candidate)


def environment():
    return (("ravel", __version__), ("python", platform.python_version()),
            ("implementation", platform.python_implementation()), ("platform", platform.platform()))


def _generate(recipe, source_document=None):
    table = recipe["table"]
    columns = []
    for field in table["fields"]:
        values = _stream(recipe["seed"], table["id"], field["id"], "values")
        missing = _stream(recipe["seed"], table["id"], field["id"], "missing")
        numerator, denominator = _ratio(field["missing_probability"])
        kind = field["kind"]
        from .extended import column as extended_column
        prepared = extended_column(recipe, field, table["row_count"], values, source_document)
        if kind == "category":
            weights = [Decimal(p) for p in field["probabilities"]]
            scale = max(-p.as_tuple().exponent for p in weights)
            total, cumulative = 0, []
            for weight in weights:
                total += int(weight * 10**scale)
                cumulative.append(total)
        if kind == "decimal":
            places = field["places"]
            low, high = (int(Decimal(field[k]) * 10**places) for k in ("minimum", "maximum"))
        column = []
        for row in range(table["row_count"]):
            if prepared is not None:
                value = prepared[row]
            elif kind == "id":
                value = field["start"] + row
            elif kind == "text_id":
                value = field["prefix"] + str(field["start"] + row).zfill(field["width"])
            elif kind == "sequence":
                value = field["start"] + row * field["step"]
            elif kind == "constant":
                value = field["value"]
            elif kind == "integer":
                value = values.randint(field["minimum"], field["maximum"])
            elif kind == "decimal":
                value = Decimal(values.randint(low, high)).scaleb(-places)
            else:
                value = field["values"][bisect_right(cumulative, values.randrange(total))]
            column.append(None if missing.randrange(denominator) < numerator else value)
        columns.append(column)
    return Result(dumps(recipe), tuple(f["name"] for f in table["fields"]),
                  tuple(zip(*columns)),
                  environment())


def cell_text(value):
    if value is None:
        return ""
    if isinstance(value, bool):
        return "true" if value else "false"
    return format(value, "f") if isinstance(value, Decimal) else str(value)


def preview_rows(result, limit=100):
    return [[cell_text(cell) for cell in row] for row in result.rows[:limit]]


def csv_text(result):
    output = StringIO(newline="")
    writer = csv.writer(output, lineterminator="\n", quoting=csv.QUOTE_ALL)
    writer.writerow(result.headers)
    writer.writerows([cell_text(cell) for cell in row] for row in result.rows)
    return output.getvalue()


def run_metadata(result):
    record = dict(environment=dict(result.environment), recipe_sha256=sha256(result.recipe_json.encode()).hexdigest(),
                csv_sha256=sha256(csv_text(result).encode()).hexdigest(), row_count=len(result.rows),
                column_count=len(result.headers), format="ravel-run/1")
    recipe = json.loads(result.recipe_json)
    if "sample" in recipe:
        from .sample import assumption_origin, context
        _, _, retained, generated = context(recipe)
        record.update(source_sha256=recipe["sample"]["sha256"], sample_mode=recipe["sample"]["mode"],
                      retained_rows=retained, generated_rows=generated,
                      assumption_origins={f['id']:{key:assumption_origin(recipe,f['id'],key) for key in f} for f in recipe['table']['fields']})
    return record
