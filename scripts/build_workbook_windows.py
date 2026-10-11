"""Build one console/one-folder workbook experiment with pinned NiceGUI tooling."""

import argparse
from importlib.metadata import version
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "outputs/workbook-windows")
    parser.add_argument("--build-lock", type=Path,
                        default=ROOT / "experiments/workbook/requirements-build.lock",
                        help="Explicit candidate build lock; the established lock remains the default.")
    args = parser.parse_args()
    if sys.platform != "win32":
        parser.error("This recipe is a Windows experiment only.")
    for lock in (ROOT / "experiments/workbook/requirements.lock", args.build_lock):
        for line in lock.read_text().splitlines():
            if "==" in line and not line.startswith("#"):
                package, expected = line.split("==")
                if version(package) != expected:
                    parser.error(f"{package} must be {expected}; install the pinned locks first.")
    output = args.output.resolve()
    if output.exists():
        parser.error("Use a new output directory to preserve previous build evidence.")
    output.mkdir(parents=True)
    command = [sys.executable, "-m", "nicegui.scripts.pack", "--onedir", "--name", "Ravel-workbook"]
    for source, destination in (("workbook.css", "experiments/workbook"),
                                ("icons", "experiments/workbook/icons"),
                                ("fixtures", "experiments/workbook/fixtures")):
        command.extend(["--add-data", f"{ROOT / 'experiments/workbook' / source}{os.pathsep}{destination}"])
    command.append(str(ROOT / "experiments/workbook/bundle_entry.py"))
    env = dict(os.environ)
    # NiceGUI 3.18.0 invokes `pyinstaller` by name on Windows.
    env["PATH"] = str(Path(sys.executable).parent) + os.pathsep + env.get("PATH", "")
    env["PYTHONPATH"] = str(ROOT)
    env["PYTHONNOUSERSITE"] = "1"
    env["PYTHONUSERBASE"] = str(output / "python-user-base")
    env["PYINSTALLER_CONFIG_DIR"] = str(output / "pyinstaller-cache")
    print(subprocess.list2cmdline(command), flush=True)
    with (output / "build.log").open("w", encoding="utf-8") as log:
        subprocess.run(command, cwd=output, env=env, stdout=log, stderr=subprocess.STDOUT, check=True)
    bundle = output / "dist/Ravel-workbook"
    # The pinned nicegui-pack wrapper does not propagate PyInstaller's exit code.
    required = [bundle / "Ravel-workbook.exe"]
    required.extend(bundle / "_internal/experiments/workbook" / path for path in
                    ("workbook.css", "icons/home.svg", "icons/save.svg", "icons/reload.svg", "fixtures/sample.csv"))
    missing = [str(path) for path in required if not path.is_file()]
    if missing:
        raise RuntimeError(f"Incomplete bundle; see {output / 'build.log'}: {missing}")
    print(f"Built {bundle}")


if __name__ == "__main__":
    main()
