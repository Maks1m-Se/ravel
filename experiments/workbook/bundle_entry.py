"""Console launcher for the bounded Windows folder-bundle experiment."""

import argparse
import json
import multiprocessing
import sys

from nicegui import ui

from experiments.workbook import app as workbook


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=8083)
    parser.add_argument("--runtime-info", action="store_true", help="Print import paths for bundle verification.")
    args = parser.parse_args()
    if args.runtime_info:
        print(json.dumps({"frozen": bool(getattr(sys, "frozen", False)),
                          "executable": sys.executable, "app": workbook.__file__,
                          "fixture": str(workbook.model.FIXTURE), "import_paths": sys.path}), flush=True)
    ui.run(host="127.0.0.1", port=args.port, title="Ravel | Workbook experiment",
           dark=True, reload=False, show=False, prod_js=True, on_air=False)


if __name__ == "__main__":
    multiprocessing.freeze_support()
    main()
