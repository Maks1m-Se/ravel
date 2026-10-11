"""Experiment state and count contracts; no claim of generated-data validation."""

from copy import deepcopy
import json
import unittest

from experiments.workbook import config as workbook


class WorkbookConfigTests(unittest.TestCase):
    def test_save_validates_field_and_output_before_replacing_applied_state(self):
        applied = workbook.new_config("sample")
        applied["output"] = {"mode": "extend", "count": 1000}
        before = deepcopy(applied)
        field = applied["table"]["fields"][-1]
        draft = {**field["settings"], "maximum": 20}
        draft_before = deepcopy(draft)
        output = {"mode": "extend", "count": 9}
        with self.assertRaisesRegex(ValueError, "at least 10"):
            applied = workbook.update_field(applied, field["id"], draft, output=output)
        self.assertEqual(applied, before)
        self.assertEqual(draft, draft_before)
        self.assertEqual(output, {"mode": "extend", "count": 9})
        output["count"] = 1000
        applied = workbook.update_field(applied, field["id"], draft, output=output)
        saved = workbook.loads(workbook.dumps(applied))
        self.assertEqual(saved["table"]["fields"][-1]["settings"], draft)
        self.assertEqual(saved["table"]["fields"][-1]["origins"]["maximum"], "user override")
        self.assertEqual(saved["output"], output)
        self.assertEqual(before["table"]["fields"][-1]["settings"]["maximum"], 12.2)

    def test_oversized_integer_import_has_readable_validation_error(self):
        config = workbook.new_config("sample")
        config["table"]["fields"][-1]["settings"]["maximum"] = 10**400
        config["table"]["fields"][-1]["origins"]["maximum"] = "user override"
        with self.assertRaisesRegex(ValueError, "Maximum must be a finite number supported by this experiment"):
            workbook.loads(json.dumps(config))

    def test_validation_identifies_both_bounds_and_missing_percentage(self):
        settings = workbook.new_config("scratch")["table"]["fields"][0]["settings"]
        settings.update(minimum=200, maximum=100, missing_percent=150)
        with self.assertRaises(workbook.ValidationError) as error:
            workbook.validate_settings(settings)
        self.assertEqual(set(error.exception.issues), {"minimum", "maximum", "missing_percent"})
        self.assertEqual(error.exception.issues["minimum"], error.exception.issues["maximum"])

    def test_both_entries_use_same_format_and_round_trip(self):
        for entry in ("scratch", "sample"):
            with self.subTest(entry=entry):
                config = workbook.new_config(entry)
                self.assertEqual(workbook.loads(workbook.dumps(config)), config)
                self.assertEqual(config["format"], workbook.FORMAT)
                self.assertEqual(set(config["table"]["fields"][-1]["settings"]), workbook.SETTINGS)

    def test_edit_preserves_basis_and_other_fields_without_mutation(self):
        config = workbook.new_config("sample")
        original = deepcopy(config)
        field = config["table"]["fields"][-1]
        settings = {**field["settings"], "maximum": 20, "missing_percent": 5}
        edited = workbook.update_field(config, field["id"], settings)
        self.assertEqual(config, original)
        self.assertEqual(edited["table"]["fields"][:-1], original["table"]["fields"][:-1])
        result = workbook.loads(workbook.dumps(edited))["table"]["fields"][-1]
        self.assertEqual(result["basis"], field["basis"])
        self.assertEqual(result["origins"]["maximum"], "user override")
        self.assertEqual(result["origins"]["minimum"], "sample suggestion")
        self.assertEqual(result["settings"]["maximum"], 20)
        reset = workbook.update_field(edited, field["id"], field["basis"])
        self.assertEqual(reset, original)

    def test_invalid_edits_are_atomic_and_correctable(self):
        config = workbook.new_config("scratch")
        before = deepcopy(config)
        field = config["table"]["fields"][0]
        for settings in ({**field["settings"], "minimum": 101},
                         {**field["settings"], "missing_percent": -1},
                         {**field["settings"], "maximum": float("nan")},
                         {**field["settings"], "name": " "}):
            with self.assertRaises(ValueError):
                workbook.update_field(config, field["id"], settings)
            self.assertEqual(config, before)
        valid = workbook.update_field(config, field["id"], {**field["settings"], "maximum": 200})
        self.assertEqual(valid["table"]["fields"][0]["settings"]["maximum"], 200)

    def test_new_and_extend_counts_and_boundaries(self):
        for entry in ("scratch", "sample"):
            config = workbook.new_config(entry)
            self.assertEqual(workbook.counts(config)["generated"], 1000)
            self.assertEqual(workbook.counts(config)["retained"], 0)
            self.assertEqual(workbook.counts(config)["total"], 1000)
        config = workbook.new_config("sample")
        config["output"]["mode"] = "extend"
        self.assertEqual(workbook.counts(config), dict(source=10, retained=10, generated=990, total=1000))
        config["output"]["count"] = 10
        self.assertEqual(workbook.counts(config)["generated"], 0)
        for invalid in (9, 0, -1, 10.5, True, 1_000_001):
            config["output"]["count"] = invalid
            with self.assertRaises(ValueError):
                workbook.counts(config)
        config = workbook.new_config("scratch")
        config["output"]["mode"] = "extend"
        with self.assertRaises(ValueError):
            workbook.counts(config)

    def test_reject_invalid_or_foreign_configuration(self):
        for content in ("not json", "[]", "null", '{"format":"future"}', "[" * 2000):
            with self.subTest(content=content[:30]), self.assertRaises(ValueError):
                workbook.loads(content)
        config = workbook.new_config("sample")
        config["table"]["fields"][-1]["origins"]["maximum"] = "default"
        with self.assertRaisesRegex(ValueError, "provenance"):
            workbook.loads(json.dumps(config))

    def test_fixture_and_precomputed_suggestions_agree(self):
        rows = workbook.source_rows()
        self.assertEqual(len(rows), 10)
        self.assertEqual(len({row["item_id"] for row in rows}), 10)
        self.assertEqual({row["material"] for row in rows}, {"steel", "aluminium", "polymer"})
        values = [float(row["length_mm"]) for row in rows]
        field = workbook.new_config("sample")["table"]["fields"][-1]
        self.assertEqual((min(values), max(values)), (9.8, 12.2))
        self.assertEqual((field["basis"]["minimum"], field["basis"]["maximum"]), (9.8, 12.2))


if __name__ == "__main__":
    unittest.main()
