# Ravel

**Compose the data you need.**

Synthetic test data from examples, assumptions and explicit rules.

Ravel is a project to build an offline synthetic test-data generator for
software testing. Clinical and biomedical scenarios will come first, backed by
a general-purpose generation engine. Windows, Linux and macOS support is planned.

## Current status

**Development preview.** The working tooling is a Python standard-library
generator and an offline progress dashboard showing current focus, tasks,
evidence and release criteria. Generation and viewing instructions are below.

The maintainer has accepted a [fictional baseline/change specification](docs/baseline-specification.md)
with explicit validation/output contracts and four hand-worked reference cases.
Clinical data generation and the application CLI/UI are not implemented.
Specification acceptance does not establish independent clinical validation or
standards conformity; no application dependencies or setup commands exist yet.

## Project documents

- [Project plan](docs/plan.md): scope, milestones, and measurable release gates.
- [Progress record](docs/progress.json): authoritative status, evidence, and next action.
- [Decisions](docs/decisions.md): agreed direction and unresolved choices.
- [Specification](docs/specification.md): accepted recipe architecture and ownership boundary; field notation remains illustrative and schema details deferred.
- [Baseline specification](docs/baseline-specification.md): accepted M0-05 fictional clinical policies, source context, validation/output contracts and four hand-worked cases; numeric prerequisites remain open and no clinical functionality is implemented.

- [Progress dashboard](docs/dashboard.html): generated, read-only offline snapshot.

## Progress dashboard

Open `docs/dashboard.html` directly in a browser. It uses no external resources.
Task counts show **Tasks completed**, not effort; tasks differ in size. Release
gates show readiness separately and require recorded evidence.

From the repository root, with Python 3.11 or later (no extra dependencies):

```sh
python scripts/build_dashboard.py
python scripts/build_dashboard.py --check
python -m unittest discover -s tests -v
git diff --check
```

Update `docs/progress.json` for statuses, tasks, blockers, evidence, and next
action. Criterion text comes from `docs/plan.md`. Regenerate and commit the
dashboard alongside changes to either source; do not edit the HTML directly.
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

`--check` validates inputs and fails if the generated snapshot is stale. Tests
check totals, determinism, escaping, invalid inputs, focus references and order,
derived record details, and resource isolation.
Browser interaction and visual review remain separate checks. These commands
verify project tracking only; they do not establish application release readiness.

## Planned direction

The intended clinical focus is invented test data for clinical and biomedical
scenarios, with explicit clinical rules and independently determined expected
results. Generic generation logic, clinical rules, and interface code will be
kept separate. These are planned capabilities, not implemented functionality.

## Development and licensing

Development is AI-assisted, including repository documentation and planned code
contributions. AI-generated work requires review and meaningful verification;
AI assistance does not establish clinical correctness.

The display name is **Ravel**; repository and folder names are `ravel`, as are
the intended Python import and CLI names. The local working folder is
`C:\Git\ravel`; the private GitHub repository is
[Maks1m-Se/ravel](https://github.com/Maks1m-Se/ravel). The public PyPI
distribution name remains unresolved. License selection is pending; no
open-source license has been granted yet.
