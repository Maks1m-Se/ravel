"""Build Ravel's offline, read-only project snapshot using only the standard library."""

import argparse
from collections import Counter
import html
import json
from pathlib import Path
import re
import sys


ROOT = Path(__file__).resolve().parents[1]
STATUSES = ("pending", "in_progress", "review", "blocked", "done")
GATE_STATUSES = ("unverified", "passed", "failed", "blocked")
LABELS = {"in_progress": "In progress", "review": "Review"}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def strings(value, context):
    require(isinstance(value, list) and all(isinstance(x, str) and x.strip() for x in value),
            f"{context}: expected a list of nonempty strings")


def text(value, context):
    require(isinstance(value, str) and bool(value.strip()), f"{context}: expected nonempty text")


def index(items, context):
    require(isinstance(items, list), f"{context}: expected a list")
    result = {}
    for item in items:
        require(isinstance(item, dict), f"{context}: expected objects")
        key = item.get("id")
        text(key, f"{context}.id")
        require(key not in result, f"{context}: duplicate ID {key}")
        result[key] = item
    return result


def plan_tables(plan):
    milestones, gates = {}, {}
    for line in plan.splitlines():
        if not line.startswith("| "):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        match = re.fullmatch(r"([MR]\d+) — (.+)", cells[0])
        if match:
            require(len(cells) == 3, f"Plan row {match[1]}: expected three columns")
            target = milestones if match[1].startswith("M") else gates
            require(match[1] not in target, f"Plan: duplicate ID {match[1]}")
            target[match[1]] = (match[2], cells[1], cells[2])
    require(set(milestones) == {f"M{i}" for i in range(7)}, "Plan must contain M0–M6")
    require(set(gates) == {f"R{i}" for i in range(1, 11)}, "Plan must contain R1–R10")
    return milestones, gates


def validate(data, plan):
    require(isinstance(data, dict), "Progress must be a JSON object")
    require(data.get("schema_version") == 1, "Unsupported progress schema_version")
    require(type(data.get("planning_revision")) is int and data["planning_revision"] > 0,
            "planning_revision must be a positive integer")
    require(data.get("plan_ref") == "docs/plan.md", "plan_ref must be docs/plan.md")
    pm, pg = plan_tables(plan)
    milestones = index(data.get("milestones"), "milestones")
    tasks = index(data.get("tasks"), "tasks")
    gates = index(data.get("release_gates"), "release_gates")
    evidence = index(data.get("evidence"), "evidence")
    require(set(milestones) == set(pm), "Progress milestones must match plan M0–M6")
    require(set(gates) == set(pg), "Progress release gates must match plan R1–R10")
    for ev in evidence.values():
        text(ev.get("reference"), f"{ev['id']}.reference")
        text(ev.get("scope"), f"{ev['id']}.scope")
    for group, statuses in ((milestones, STATUSES), (tasks, STATUSES), (gates, GATE_STATUSES)):
        for key, item in group.items():
            require(item.get("status") in statuses, f"{key}: invalid status {item.get('status')!r}")
            strings(item.get("evidence_refs"), f"{key}.evidence_refs")
            require(set(item["evidence_refs"]) <= set(evidence), f"{key}: unknown evidence reference")
            if group is not gates:
                text(item.get("title"), f"{key}.title")
                strings(item.get("blockers"), f"{key}.blockers")
            if group is milestones:
                require(item.get("acceptance_criteria_ref") == data["plan_ref"], f"{key}: invalid plan reference")
            if group is gates:
                require(item.get("criterion_ref") == data["plan_ref"], f"{key}: invalid criterion reference")
                require(item["status"] != "passed" or item["evidence_refs"], f"{key}: passed gate needs evidence")
            if group is tasks:
                require(item.get("milestone_id") in milestones, f"{key}: unknown milestone")
                require(re.fullmatch(re.escape(item["milestone_id"]) + r"-\d+", key), f"{key}: ID must belong to milestone")
                strings(item.get("acceptance_criteria"), f"{key}.acceptance_criteria")
                require(item["acceptance_criteria"], f"{key}: acceptance criteria required")
                strings(item.get("release_gate_ids"), f"{key}.release_gate_ids")
                require(set(item["release_gate_ids"]) <= set(gates), f"{key}: unknown release gate")
    strings(data.get("blockers"), "project.blockers")
    text(data.get("next_action"), "next_action")
    return pm, pg, evidence


def esc(value):
    return html.escape(str(value), quote=True)


def badge(status):
    return f'<span class="badge {esc(status)}">{esc(LABELS.get(status, status.capitalize()))}</span>'


def listing(items, empty="None recorded."):
    return "<ul>" + "".join(f"<li>{esc(x)}</li>" for x in items) + "</ul>" if items else f"<p class=muted>{esc(empty)}</p>"


def evidence_html(refs, evidence):
    return listing([f"{ref} · {evidence[ref]['reference']} — {evidence[ref]['scope']}" for ref in refs],
                   "No evidence recorded.")


STYLE = """
:root{color-scheme:light;--ink:#24332d;--muted:#59665f;--green:#285c45;--line:#d7dfd8;--paper:#fff}
*{box-sizing:border-box}body{margin:0;background:#f3f5f1;color:var(--ink);font:16px/1.6 system-ui,sans-serif}
main{max-width:1120px;margin:auto;padding:40px 24px 64px}h1,h2,h3,p{margin:0 0 12px}h1{font-size:48px;letter-spacing:-2px;line-height:1.1}h2{font-size:23px}h3{font-size:18px}
header{margin-bottom:28px}.eyebrow{color:var(--green);font-size:13px;font-weight:700;letter-spacing:1px;text-transform:uppercase}.tagline{font-size:24px;margin-top:12px}.muted,small{color:var(--muted)}
section{margin-top:28px}.panel,details.milestone,.gate{background:var(--paper);border:1px solid var(--line);border-radius:12px;padding:22px}.next{border-left:5px solid var(--green)}
.counts{display:grid;grid-template-columns:repeat(5,1fr);gap:12px}.count{background:white;padding:16px;border:1px solid var(--line);border-radius:10px}.count strong{display:block;font-size:28px}
.badge{display:inline-block;font-size:13px;font-weight:650;padding:2px 10px;border-radius:20px;background:#edf0ed;color:#39463e;white-space:nowrap}.done,.passed{background:#e0eee5;color:#20543d}.review{background:#fff0d2;color:#725014}.blocked,.failed{background:#f8e4e1;color:#823d35}.in_progress{background:#dfebe7;color:#285c45}
.filters{display:flex;flex-wrap:wrap;gap:16px;align-items:end;margin:18px 0}.filters label{display:flex;flex:1;min-width:170px;flex-direction:column;gap:6px;font-weight:600}input,select,button{font:inherit;color:inherit;background:white;border:1px solid #87978c;border-radius:6px;padding:9px 12px}button{cursor:pointer}
:focus-visible{outline:3px solid #276947;outline-offset:4px}summary{cursor:pointer;min-height:38px}summary .badge{margin-left:10px}summary strong{font-size:18px}details.milestone{margin-bottom:14px}details.task{border-top:1px solid var(--line);padding:16px 0}details.task:last-child{padding-bottom:0}details.task summary{font-weight:600}details.task p,details.task h3{margin-top:14px}ul{padding-left:22px;margin:8px 0 14px}li{overflow-wrap:anywhere}.gates{display:grid;grid-template-columns:repeat(2,1fr);gap:14px}.gate h3{margin-bottom:10px}.gate .badge{margin-bottom:12px}footer{margin-top:32px;font-size:14px}code{font-size:14px;overflow-wrap:anywhere}a{color:var(--green)}[hidden]{display:none!important}
@media(max-width:700px){main{padding:24px 16px}.counts{grid-template-columns:repeat(2,1fr)}.gates{grid-template-columns:1fr}.panel,details.milestone,.gate{padding:16px}h1{font-size:40px}.tagline{font-size:21px}}
"""

SCRIPT = """
const search = document.getElementById('search');
const milestone = document.getElementById('milestone');
const status = document.getElementById('status');
const tasks = [...document.querySelectorAll('.task')];
function filter() {
  const query = search.value.trim().toLowerCase();
  let visible = 0;
  for (const task of tasks) {
    const match = (!milestone.value || task.dataset.milestone === milestone.value)
      && (!status.value || task.dataset.status === status.value)
      && (!query || task.textContent.toLowerCase().includes(query));
    task.hidden = !match;
    visible += Number(match);
  }
  const active = Boolean(query || milestone.value || status.value);
  for (const group of document.querySelectorAll('.milestone')) {
    group.hidden = ![...group.querySelectorAll('.task')].some(task => !task.hidden);
    if (active && !group.hidden) group.open = true;
  }
  document.getElementById('results').textContent = `${visible} of ${tasks.length} tasks shown`;
}
for (const control of [search, milestone, status]) control.addEventListener('input', filter);
document.getElementById('reset').addEventListener('click', () => {
  search.value = ''; milestone.value = ''; status.value = ''; filter(); search.focus();
});
filter();
"""


def render(data, plan):
    pm, pg, evidence = validate(data, plan)
    counts = Counter(t["status"] for t in data["tasks"])
    total = len(data["tasks"])
    percentage = counts["done"] * 100 / total if total else 0
    cards = "".join(f'<div class=count data-count-status="{s}"><strong>{counts[s]}</strong>{badge(s)}</div>' for s in STATUSES)
    groups = []
    for milestone in data["milestones"]:
        mid = milestone["id"]
        tasks = []
        for task in data["tasks"]:
            if task["milestone_id"] != mid:
                continue
            tasks.append(f'''<details class="task" data-milestone="{mid}" data-status="{task['status']}" id="{esc(task['id'])}">
<summary>{esc(task['id'])} · {esc(task['title'])} {badge(task['status'])}</summary>
<h3>Acceptance criteria</h3>{listing(task['acceptance_criteria'])}
<h3>Blockers</h3>{listing(task['blockers'])}
<h3>Evidence</h3>{evidence_html(task['evidence_refs'], evidence)}
<p class=muted>Release gates: {esc(', '.join(task['release_gate_ids']) or 'None linked')}</p></details>''')
        groups.append(f'''<details class="milestone" {'open' if mid == 'M0' else ''}>
<summary><strong>{mid} · {esc(milestone['title'])}</strong> {badge(milestone['status'])} <small>· {len(tasks)} tasks</small></summary>
<p>Deliverable: {esc(pm[mid][1])}</p><p>Exit condition: {esc(pm[mid][2])}</p>
<h3>Milestone blockers</h3>{listing(milestone['blockers'])}
<h3>Milestone evidence</h3>{evidence_html(milestone['evidence_refs'], evidence)}{''.join(tasks)}</details>''')
    gates = []
    for gate in data["release_gates"]:
        gid = gate["id"]
        gates.append(f'''<article class=gate><h3>{gid} · {esc(pg[gid][0])}</h3>{badge(gate['status'])}
<p>{esc(pg[gid][1])}</p><h3>Required evidence</h3><p>{esc(pg[gid][2])}</p>
<h3>Recorded evidence</h3>{evidence_html(gate['evidence_refs'], evidence)}</article>''')
    gate_counts = Counter(g['status'] for g in data['release_gates'])
    gate_summary = ' · '.join(f"{gate_counts[s]} {s}" for s in GATE_STATUSES)
    options = ''.join(f'<option value="{m["id"]}">{m["id"]} · {esc(m["title"])}</option>' for m in data['milestones'])
    statuses = ''.join(f'<option value="{s}">{esc(LABELS.get(s, s.capitalize()))}</option>' for s in STATUSES)
    return f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'; script-src 'unsafe-inline'; connect-src 'none'; base-uri 'none'; form-action 'none'">
<title>Ravel · Project progress</title><style>{STYLE}</style></head>
<body><main><header><p class=eyebrow>Project progress · Planning revision {data['planning_revision']}</p>
<h1>Ravel</h1><p class=tagline>Compose the data you need.</p>
<p>Synthetic test data from examples, assumptions and explicit rules.</p>
<p class=muted>Planning and foundation work. Application capabilities are planned; release readiness requires evidence.</p></header>
<section class="panel next" aria-labelledby="next"><h2 id=next>Next action</h2><p>{esc(data['next_action'])}</p>
<h3>Project blockers</h3>{listing(data['blockers'])}</section>
<section aria-labelledby="overview"><h2 id=overview>Task overview</h2><div class=counts>{cards}</div>
<p style="margin-top:16px"><strong>Tasks completed: {percentage:.1f}%</strong> · {counts['done']} of {total} tasks. Tasks differ in size; this is a count, not an effort estimate.</p></section>
<section aria-labelledby="milestones"><h2 id=milestones>Milestones and tasks</h2>
<p class=muted>Search task titles, acceptance criteria, blockers and evidence. Filters affect tasks only; overview counts and release gates show the full project.</p>
<div class=filters><label for=search>Search tasks<input id=search type=search placeholder="Find a task…"></label>
<label for=milestone>Milestone<select id=milestone><option value="">All milestones</option>{options}</select></label>
<label for=status>Task status<select id=status><option value="">All statuses</option>{statuses}</select></label>
<button id=reset type=button>Reset filters</button></div><p id=results role=status aria-live=polite></p>
<noscript><p>Enable JavaScript for search and filters. All task details remain readable without it.</p></noscript>{''.join(groups)}</section>
<section aria-labelledby="gates"><h2 id=gates>Release-gate readiness</h2><p>{esc(gate_summary)} · {gate_counts['passed']} of 10 gates passed.</p>
<p class=muted>Criteria and required evidence come from docs/plan.md. Status and recorded evidence come from docs/progress.json. Task completion does not establish release readiness.</p>
<div class=gates>{''.join(gates)}</div></section>
<footer class=panel><strong>Generated, read-only snapshot.</strong> Update <code>docs/progress.json</code>, then run
<code>python scripts/build_dashboard.py</code> from the repository root. Regenerate after changes to <code>docs/plan.md</code> too.
Review and commit the snapshot with its source changes. Check it with <code>python scripts/build_dashboard.py --check</code>.</footer>
</main><script>{SCRIPT}</script></body></html>
'''


def load(progress, plan):
    def unique_object(pairs):
        obj = {}
        for key, value in pairs:
            require(key not in obj, f"JSON: duplicate key {key}")
            obj[key] = value
        return obj
    def invalid_constant(value):
        raise ValueError(f"JSON: invalid constant {value}")
    data = json.loads(progress.read_text(encoding="utf-8"), object_pairs_hook=unique_object,
                      parse_constant=invalid_constant)
    return render(data, plan.read_text(encoding="utf-8"))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--progress", type=Path, default=ROOT / "docs/progress.json")
    parser.add_argument("--plan", type=Path, default=ROOT / "docs/plan.md")
    parser.add_argument("--output", type=Path, default=ROOT / "docs/dashboard.html")
    parser.add_argument("--check", action="store_true", help="validate inputs and fail if snapshot is stale")
    args = parser.parse_args()
    try:
        content = load(args.progress, args.plan).encode("utf-8")
        if args.check:
            require(args.output.read_bytes() == content, "Dashboard is stale; run python scripts/build_dashboard.py")
            print("Dashboard inputs valid; snapshot is current.")
        else:
            args.output.write_bytes(content)
            print(f"Built {args.output}")
    except (OSError, ValueError, KeyError, TypeError) as error:
        print(f"Dashboard error: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
