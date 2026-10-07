# Ravel

**Compose the data you need.**

Synthetic test data from examples, assumptions and explicit rules.

A planned free, open-source, offline test-data generator for Windows, Linux,
and macOS. Clinical and biomedical scenarios will come first, supported by a
general-purpose generation engine.

## Current status

**Planning and repository setup.** This repository contains foundation
documentation, planning records, and a standard-library progress dashboard
generator. Application functionality is not implemented; no application
dependencies or application setup commands exist yet.

## Project documents

- [Project plan](docs/plan.md): scope, milestones, and measurable release gates.
- [Progress record](docs/progress.json): authoritative status, evidence, and next action.
- [Decisions](docs/decisions.md): agreed direction and unresolved choices.

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
`--check` validates inputs and fails if the generated snapshot is stale. Tests
check totals, determinism, escaping, invalid inputs, and resource isolation.
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
