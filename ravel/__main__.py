"""CLI adapter for the shared recipe and engine."""

import argparse
import json
from pathlib import Path
import sys

from .engine import csv_text, generate, run_metadata
from .recipe import MAX_BYTES, ValidationError, loads


def read_recipe(path):
    with path.open("rb") as source:
        return loads(source.read(MAX_BYTES + 1))


def write_outputs(input_path, csv_path, result):
    paths = [csv_path, csv_path.with_suffix(".recipe.json"), csv_path.with_suffix(".run.json")]
    resolved = [path.resolve() for path in paths]
    if len(set(resolved)) != len(paths) or input_path.resolve() in resolved:
        raise ValueError("Output files must be distinct from one another and from the input recipe.")
    for path in paths:
        if path.exists():
            raise FileExistsError(f"Output already exists: {path}. Choose another CSV filename; existing files are never overwritten.")
    payloads = [csv_text(result), result.recipe_json, json.dumps(run_metadata(result), indent=2) + "\n"]
    created = []
    try:
        for path, payload in zip(paths, payloads):
            with path.open("xb") as output:
                created.append(path)
                output.write(payload.encode("utf-8"))
    except OSError:
        for path in created:
            path.unlink()
        raise
    return paths


def main(argv=None):
    parser = argparse.ArgumentParser(prog="python -m ravel", description="Generate one table from explicit rules.")
    commands = parser.add_subparsers(dest="command", required=True)
    check = commands.add_parser("validate", help="Validate a versioned recipe without generating.")
    check.add_argument("recipe", type=Path)
    run = commands.add_parser("generate", help="Write CSV, canonical recipe and run metadata; never overwrite files.")
    run.add_argument("recipe", type=Path)
    run.add_argument("--csv", type=Path, required=True)
    commands.add_parser("ui", help="Launch the local table builder (requires requirements-ui.lock).")
    args = parser.parse_args(argv)
    try:
        if args.command == "ui":
            from .ui import launch
            launch()
            return 0
        recipe = read_recipe(args.recipe)
        if args.command == "validate":
            print(f"Valid {recipe['format']}: {len(recipe['table']['fields'])} columns, {recipe['table']['row_count']:,} rows.")
        else:
            result = generate(recipe)
            paths = write_outputs(args.recipe, args.csv, result)
            print(f"Generated {len(result.rows):,} rows; wrote " + ", ".join(str(p) for p in paths))
        return 0
    except (ValidationError, OSError, ValueError) as exc:
        print(f"Ravel: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
