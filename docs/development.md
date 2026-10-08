# Development guide

The runnable tooling currently builds a read-only progress dashboard using
Python's standard library. Clinical generation and the application CLI/UI are
not implemented; no application dependencies or setup commands exist yet.

## View and check the dashboard

Open [dashboard.html](dashboard.html) directly in a browser. It uses no external
resources. Task counts show **Tasks completed**, not effort; tasks differ in
size. Release gates show readiness separately and require recorded evidence.

From the repository root, with Python 3.11 or later (no extra dependencies):

```sh
python scripts/build_dashboard.py
python scripts/build_dashboard.py --check
python -m unittest discover -s tests -v
git diff --check
```

The [generator](../scripts/build_dashboard.py) reads the maintained documents;
[tracking tests](../tests/test_dashboard.py) check totals, determinism, escaping,
invalid inputs, focus references and order, derived record details, and resource
isolation. `--check` validates inputs and fails if the generated snapshot is
stale. Browser interaction and visual review remain separate checks. These
commands verify project tracking only; they do not establish application or
clinical validation or release readiness.

## Maintain progress

[progress.json](progress.json) is the authoritative record of statuses, tasks,
blockers, evidence and next action. Criterion text comes from [plan.md](plan.md).
Regenerate and commit the dashboard alongside changes to either source; do not
edit the HTML directly. Record significant decisions in [decisions.md](decisions.md).
Issues may support discussion without creating a second status record.

The focus panel uses `current_task_id` and ordered `next_task_ids` (up to two)
from progress.json, deriving titles, statuses and the current milestone from
existing records. `next_action` supplies the concrete action. It shows project,
current-milestone and current-task blockers when recorded. Task links open
details and clear filters only when necessary to reveal the target; use Tab and
Enter to follow a link, and Enter or Space on a task summary to toggle details.

When the maintainer accepts a task, mark it done and advance `current_task_id`
to the next agreed unfinished task in the same update. Remove that task from
`next_task_ids`, record the next agreed order, and update `next_action`. Do not
select completed, duplicate or unknown task IDs. Focus is explicitly maintained,
not inferred from statuses or task-ID order. Regenerate the dashboard afterward.
Preserve historical evidence and its stated scope and limitations.

## Review documentation

The [README](../README.md) introduces the project; the
[clinical specification](baseline-specification.md) is the source for its four
reference cases, and [specification.md](specification.md) defines the accepted
recipe architecture. The clinical contracts and numeric prerequisites remain
separate from presentation changes. Examples are specification reference
expectations, not executed application outputs or independent clinical validation.

Optional presentation check: view the README in a Markdown renderer with
Mermaid support. Expect four case rows with baseline/change pairs 10/+3, 8/+3,
null/null and 10/+5, plus one diagram explicitly labelled as planned architecture.
Follow the local document and license links. This checks presentation and links,
not clinical correctness. In the dashboard, check filtering, task-link navigation,
keyboard expansion and visible focus after changes that affect those behaviours.

## Contributor and release preparation

Follow [AGENTS.md](../AGENTS.md) and the [plan](plan.md): work in small, reviewable
changes, use invented fixtures, and keep confidential data and credentials out
of version control. Local Codex implements changes; the ChatGPT Project handles
planning and review, and the maintainer accepts results. Critical clinical
choices and important user-facing behaviour require maintainer review.

The approved [MIT license](../LICENSE) is present. M0-07 still requires the
remaining contributor/release rules and dependency/license review before public
alpha; adding the license and this guide does not complete the task or any
release gate. Consult [progress.json](progress.json) for current blockers and the
required next action. The maintainer accepted residual email discoverability in
retained GitHub history; the [decision record](decisions.md) preserves that
acceptance and the earlier findings without claiming complete removal.
