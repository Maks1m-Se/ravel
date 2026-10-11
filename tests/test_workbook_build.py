"""Check lock selection without launching a packaging subprocess."""

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts import build_workbook_windows as build


class BuildLockTests(unittest.TestCase):
    def run_recipe(self, lock=None, setuptools_version="65.5.0", missing_brand_asset=None):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "build"
            argv = ["build_workbook_windows.py", "--output", str(output)]
            if lock:
                argv += ["--build-lock", str(lock)]
            pins = {}
            for path in (build.ROOT / "experiments/workbook/requirements.lock",
                         build.ROOT / "experiments/workbook/requirements-build.lock"):
                pins.update(line.split("==") for line in path.read_text().splitlines()
                            if "==" in line and not line.startswith("#"))
            pins["setuptools"] = setuptools_version

            def create_bundle(*args, **kwargs):
                bundle = output / "dist/Ravel-workbook"
                paths = ["Ravel-workbook.exe"] + [
                    "_internal/experiments/workbook/" + asset for asset in
                    ("workbook.css", "icons/home.svg", "icons/save.svg",
                     "icons/reload.svg", "fixtures/sample.csv")]
                paths += ["_internal/brand/" + asset for asset in (
                    "svg/ravel-mark-32-light.svg", "svg/ravel-mark-32-dark.svg",
                    "favicon/favicon.svg", "favicon/favicon.ico") if asset != missing_brand_asset]
                for path in paths:
                    target = bundle / path
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.touch()

            with patch.object(build.sys, "argv", argv), patch.object(build.sys, "platform", "win32"), \
                    patch.object(build, "version", side_effect=pins.__getitem__), \
                    patch.object(build.subprocess, "run", side_effect=create_bundle) as package:
                build.main()
                self.assertEqual(package.call_count, 1)

    def test_default_accepts_established_lock(self):
        self.run_recipe()

    def test_candidate_requires_explicit_selection(self):
        with self.assertRaises(SystemExit) as error:
            self.run_recipe(setuptools_version="80.9.0")
        self.assertEqual(error.exception.code, 2)

    def test_explicit_candidate_accepts_replacement(self):
        self.run_recipe(build.ROOT / "experiments/workbook/requirements-build-python314-candidate.lock",
                        setuptools_version="80.9.0")

    def test_incomplete_branding_fails_build(self):
        with self.assertRaisesRegex(RuntimeError, "favicon.svg"):
            self.run_recipe(missing_brand_asset="favicon/favicon.svg")


if __name__ == "__main__":
    unittest.main()
