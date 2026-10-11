"""Provisional configuration and count arithmetic; no profiling or generation."""

from copy import deepcopy
import csv
import json
import math
from pathlib import Path


FORMAT = "ravel-workbook-experiment/1"
FIXTURE = Path(__file__).parent / "fixtures" / "sample.csv"
SETTINGS = {"name", "kind", "minimum", "maximum", "missing_percent"}
KINDS = {"number", "text"}


class ValidationError(ValueError):
    """Readable validation failure with the settings that need correction."""

    def __init__(self, issues):
        self.issues = issues
        super().__init__(" ".join(dict.fromkeys(issues.values())))


def source_rows():
    with FIXTURE.open(encoding="utf-8", newline="") as stream:
        return list(csv.DictReader(stream))


def field(identifier, name, kind, minimum, maximum, origin):
    settings = dict(name=name, kind=kind, minimum=minimum, maximum=maximum,
                    missing_percent=0)
    return dict(id=identifier, settings=settings, basis=deepcopy(settings),
                origins={key: origin for key in SETTINGS})


def new_config(entry):
    if entry not in {"scratch", "sample"}:
        raise ValueError("Choose scratch or sample.")
    if entry == "sample":
        # Deliberately written expectations for the bundled fixture, not inference.
        fields = [field("item_id", "item_id", "text", None, None, "sample suggestion"),
                  field("material", "material", "text", None, None, "sample suggestion"),
                  field("length_mm", "length_mm", "number", 9.8, 12.2, "sample suggestion")]
    else:
        fields = [field("field_1", "value", "number", 0, 100, "default")]
    return dict(format=FORMAT, entry=entry,
                table=dict(id="table_1", name="Sample table" if entry == "sample" else "New table",
                           source="bundled-sample-v1" if entry == "sample" else None,
                           fields=fields), output=dict(mode="new", count=1000))


def finite_number(value, label):
    try:
        valid = type(value) in {int, float} and math.isfinite(value)
    except OverflowError:
        valid = False
    if not valid:
        raise ValueError(f"{label} must be a finite number supported by this experiment.")


def validate_settings(settings):
    if not isinstance(settings, dict) or set(settings) != SETTINGS:
        raise ValueError("Field settings do not match this provisional format.")
    issues = {}
    name = settings["name"]
    if not isinstance(name, str) or not name.strip() or len(name) > 40:
        issues["name"] = "Field name must contain 1 to 40 characters."
    if settings["kind"] not in KINDS:
        issues["kind"] = "Field type must be number or text."
    if settings["kind"] == "number":
        for key, label in (("minimum", "Minimum"), ("maximum", "Maximum")):
            try:
                finite_number(settings[key], label)
            except ValueError as exc:
                issues[key] = str(exc)
        if not (issues.keys() & {"minimum", "maximum"}) and settings["minimum"] > settings["maximum"]:
            for key in ("minimum", "maximum"):
                issues[key] = "Minimum must not exceed maximum."
    elif settings["minimum"] is not None or settings["maximum"] is not None:
        issues["kind"] = "Text fields do not have numeric bounds."
    try:
        finite_number(settings["missing_percent"], "Missing percent")
        if not 0 <= settings["missing_percent"] <= 100:
            issues["missing_percent"] = "Missing percent must be between 0 and 100."
    except ValueError as exc:
        issues["missing_percent"] = str(exc)
    if issues:
        raise ValidationError(issues)


def counts(config):
    output = config["output"]
    target = output["count"]
    if type(target) is not int or not 1 <= target <= 1_000_000:
        raise ValidationError({"count": "Row count must be a whole number from 1 to 1,000,000."})
    if output["mode"] == "new":
        return dict(source=10 if config["entry"] == "sample" else 0,
                    retained=0, generated=target, total=target)
    if output["mode"] != "extend" or config["entry"] != "sample":
        raise ValidationError({"mode": "Extend requires the bundled ten-row sample."})
    if target < 10:
        raise ValidationError({"count": "Total must be at least 10 to retain all ten source rows."})
    return dict(source=10, retained=10, generated=target - 10, total=target)


def validate(config):
    try:
        if set(config) != {"format", "entry", "table", "output"} or config["format"] != FORMAT:
            raise ValueError("Unsupported configuration format. Expected " + FORMAT + ".")
        initial = new_config(config["entry"])
        table = config["table"]
        if set(table) != set(initial["table"]) or any(
                table[key] != initial["table"][key] for key in ("id", "name", "source")):
            raise ValueError("This experiment only supports its fixed table and source.")
        if len(table["fields"]) != len(initial["table"]["fields"]):
            raise ValueError("Unexpected field list for this entry path.")
        names = []
        for current, original in zip(table["fields"], initial["table"]["fields"]):
            if set(current) != set(original) or current["id"] != original["id"] or current["basis"] != original["basis"]:
                raise ValueError("Field identity and original suggestions must be preserved.")
            validate_settings(current["settings"])
            if set(current["origins"]) != SETTINGS:
                raise ValueError("Missing setting provenance.")
            for key, value in current["settings"].items():
                expected = original["origins"][key] if value == original["basis"][key] else "user override"
                if current["origins"][key] != expected:
                    raise ValueError("Setting provenance does not match the original suggestion.")
            names.append(current["settings"]["name"].strip().casefold())
        if len(names) != len(set(names)):
            raise ValidationError({"name": "Field names must be unique in the table."})
        if set(config["output"]) != {"mode", "count"}:
            raise ValueError("Unexpected output settings.")
        counts(config)
    except (TypeError, KeyError, AttributeError) as exc:
        raise ValueError("Invalid configuration structure.") from exc
    return config


def update_field(config, identifier, settings, *, output=None):
    """Build a complete validated candidate without changing the applied config."""
    candidate = deepcopy(config)
    selected = next(f for f in candidate["table"]["fields"] if f["id"] == identifier)
    selected["settings"] = deepcopy(settings)
    origin = "sample suggestion" if candidate["entry"] == "sample" else "default"
    selected["origins"] = {key: origin if value == selected["basis"][key] else "user override"
                           for key, value in settings.items()}
    if output is not None:
        candidate["output"] = deepcopy(output)
    return validate(candidate)


def dumps(config):
    return json.dumps(validate(config), indent=2, sort_keys=True, allow_nan=False) + "\n"


def loads(content):
    if len(content) > 65536:
        raise ValueError("Configuration must be at most 64 KiB.")
    try:
        return validate(json.loads(content))
    except (json.JSONDecodeError, UnicodeDecodeError, RecursionError) as exc:
        raise ValueError("Choose a valid experiment JSON configuration.") from exc
