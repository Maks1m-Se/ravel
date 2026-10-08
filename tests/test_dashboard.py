"""Checks for the generated project snapshot; invented hostile/invalid inputs only."""

from collections import Counter
from copy import deepcopy
from html.parser import HTMLParser
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("dashboard", ROOT / "scripts/build_dashboard.py")
dashboard = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(dashboard)


class Document(HTMLParser):
    def __init__(self, source):
        super().__init__()
        self.counts = {}
        self.tags = []
        self.attrs = []
        self.current_count = None
        self.feed(source)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        self.tags.append(tag)
        self.attrs.append(attrs)
        if "data-count-status" in attrs:
            self.current_count = attrs["data-count-status"]

    def handle_data(self, value):
        if self.current_count and value.strip().isdigit():
            self.counts[self.current_count] = int(value)
            self.current_count = None


class DashboardTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads((ROOT / "docs/progress.json").read_text(encoding="utf-8"))
        cls.plan = (ROOT / "docs/plan.md").read_text(encoding="utf-8")

    def test_snapshot_totals_and_determinism(self):
        source = dashboard.render(self.data, self.plan)
        self.assertEqual(source, dashboard.render(deepcopy(self.data), self.plan))
        self.assertEqual(source.encode("utf-8"), (ROOT / "docs/dashboard.html").read_bytes())
        counts = Counter(t["status"] for t in self.data["tasks"])
        self.assertEqual(Document(source).counts, {s: counts[s] for s in dashboard.STATUSES})
        document = Document(source)
        self.assertEqual(sum(a.get("class") == "task" for a in document.attrs), len(self.data["tasks"]))
        self.assertEqual(sum(a.get("class") == "gate" for a in document.attrs), 10)

    def test_plan_is_criterion_source(self):
        edited = self.plan.replace("All 12 reference cases", "Invented altered criterion")
        self.assertIn("Invented altered criterion", dashboard.render(self.data, edited))
        for _, criterion, evidence in dashboard.plan_tables(self.plan)[1].values():
            source = dashboard.render(self.data, self.plan)
            self.assertIn(dashboard.esc(criterion), source)
            self.assertIn(dashboard.esc(evidence), source)

    def test_imported_text_is_escaped(self):
        data = deepcopy(self.data)
        hostile = '</script><img src="https://invalid.example/" onerror="alert(1)">&'
        data["tasks"][0]["title"] = hostile
        data["tasks"][0]["acceptance_criteria"] = [hostile]
        data["tasks"][0]["blockers"] = [hostile]
        data["milestones"][0]["title"] = hostile
        data["evidence"][0]["reference"] = hostile
        data["evidence"][0]["scope"] = hostile
        data["blockers"] = [hostile]
        data["next_action"] = hostile
        source = dashboard.render(data, self.plan.replace("All 12 reference cases", hostile))
        self.assertNotIn(hostile, source)
        self.assertIn(dashboard.esc(hostile), source)
        self.assertNotIn("img", Document(source).tags)
        self.assertEqual(Document(source).tags.count("script"), 1)

    def test_invalid_references_statuses_and_ids(self):
        mutations = [
            lambda d: d["tasks"].append(deepcopy(d["tasks"][0])),
            lambda d: d["tasks"][0].update(status="invented"),
            lambda d: d["tasks"][0].update(milestone_id="M99"),
            lambda d: d["tasks"][0].update(evidence_refs=["E999"]),
            lambda d: d["tasks"][0].update(release_gate_ids=["R99"]),
            lambda d: d["release_gates"].pop(),
            lambda d: d["release_gates"][0].update(status="passed"),
            lambda d: d.update(plan_ref="other.md"),
            lambda d: d["tasks"][0].update(acceptance_criteria="wrong shape"),
        ]
        for mutation in mutations:
            with self.subTest(mutation=mutation):
                data = deepcopy(self.data)
                mutation(data)
                with self.assertRaises(ValueError):
                    dashboard.render(data, self.plan)
        with self.assertRaisesRegex(ValueError, "Plan must contain"):
            dashboard.render(self.data, self.plan.replace("| R10 —", "| R99 —"))

    def test_no_external_resources(self):
        source = dashboard.render(self.data, self.plan)
        document = Document(source)
        for attrs in document.attrs:
            self.assertFalse(set(attrs) & {"src", "srcset", "action", "poster", "data"})
            if "href" in attrs:
                self.assertIn(attrs["href"], {"#" + t["id"] for t in self.data["tasks"]})
        self.assertNotIn("@import", dashboard.STYLE)
        self.assertNotIn("url(", dashboard.STYLE)
        self.assertNotRegex(dashboard.SCRIPT, r"fetch\(|XMLHttpRequest|WebSocket|import\(")
        self.assertIn("connect-src 'none'", source)

    def test_focus_order_and_derived_records(self):
        data = deepcopy(self.data)
        data["current_task_id"] = "M1-01"
        data["next_task_ids"] = ["M0-06", "M0-05"]
        current = next(t for t in data["tasks"] if t["id"] == "M1-01")
        current.update(title="Invented current title", status="blocked", blockers=["Task obstacle"])
        data["milestones"][1].update(title="Invented milestone", blockers=["Milestone obstacle"])
        data["blockers"] = ["Project obstacle"]
        data["next_action"] = "Resolve the invented obstacle"
        source = dashboard.render(data, self.plan)
        focus = source.split('<section class="panel focus"', 1)[1].split('</section>', 1)[0]
        links = [a["href"] for a in Document(focus).attrs if a.get("class") == "task-link"]
        self.assertEqual(links, ["#M1-01", "#M0-06", "#M0-05"])
        for value in ("M1 · Invented milestone", "Invented current title", "Blocked",
                      data["next_action"], "Project obstacle", "Milestone obstacle", "Task obstacle"):
            self.assertIn(value, focus)
        self.assertLess(source.index('id="focus-title"'), source.index('class=tagline'))
        self.assertLess(source.index('id="focus-title"'), source.index('id=overview'))
        data["next_task_ids"] = []
        self.assertIn('None recorded.', dashboard.focus_html(data))

    def test_focus_rejects_invalid_selections(self):
        cases = [
            ({"current_task_id": "M99-01"}, "unknown task"),
            ({"next_task_ids": ["M99-01"]}, "unknown task"),
            ({"current_task_id": "M0-01"}, "completed task"),
            ({"next_task_ids": ["M0-01"]}, "completed task"),
            ({"next_task_ids": ["M0-05", "M0-05"]}, "duplicate"),
            ({"next_task_ids": [self.data["current_task_id"]]}, "duplicate"),
            ({"next_task_ids": ["M0-05", "M0-06", "M0-07"]}, "at most two"),
            ({"current_task_id": None}, "current_task_id"),
            ({"next_task_ids": "M0-05"}, "next_task_ids"),
        ]
        for changes, message in cases:
            with self.subTest(changes=changes):
                data = deepcopy(self.data)
                data.update(changes)
                with self.assertRaisesRegex(ValueError, message):
                    dashboard.render(data, self.plan)

    def test_focus_escapes_content_and_omits_empty_blockers(self):
        data = deepcopy(self.data)
        data["blockers"] = []
        hostile = '<img src="https://invalid.example/" onerror="alert(1)">'
        current = next(t for t in data["tasks"] if t["id"] == data["current_task_id"])
        current["title"] = hostile
        current["blockers"] = [hostile]
        focus = dashboard.focus_html(data)
        self.assertNotIn(hostile, focus)
        self.assertIn(dashboard.esc(hostile), focus)
        self.assertNotIn('Project blockers', focus)
        current["blockers"] = []
        self.assertNotIn('focus-blockers', dashboard.focus_html(data))

    def test_cli_errors_and_stale_snapshot(self):
        with tempfile.TemporaryDirectory() as folder:
            progress = Path(folder) / "progress.json"
            output = Path(folder) / "dashboard.html"
            output.write_text("Keep existing output", encoding="utf-8")
            command = [sys.executable, str(ROOT / "scripts/build_dashboard.py"),
                       "--progress", str(progress), "--output", str(output)]
            for invalid in ('{', '{"schema_version":1,"schema_version":1}', '{"invalid":NaN}',
                            json.dumps({**self.data, "tasks": [] , "next_action": None}),
                            json.dumps({**self.data, "current_task_id": "M99-01"})):
                progress.write_text(invalid, encoding="utf-8")
                result = subprocess.run(command, capture_output=True, text=True)
                self.assertEqual(result.returncode, 1)
                self.assertIn("Dashboard error:", result.stderr)
                self.assertNotIn("Traceback", result.stderr)
                self.assertEqual(output.read_text(encoding="utf-8"), "Keep existing output")
            progress.write_text(json.dumps(self.data), encoding="utf-8")
            result = subprocess.run(command + ["--check"], capture_output=True, text=True)
            self.assertEqual(result.returncode, 1)
            self.assertIn("Dashboard is stale", result.stderr)
            result = subprocess.run(command, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            first = output.read_bytes()
            result = subprocess.run(command, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(first, output.read_bytes())
            result = subprocess.run(command + ["--check"], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()
