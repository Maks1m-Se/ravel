# Repository instructions

- Read relevant current repository documentation before implementation.
- Work in small, reviewable tasks with observable acceptance criteria.
- Establish clinical rules and independently determined expected results before
  implementing derivations.
- Use invented fixtures. Keep confidential data and credentials outside version
  control.
- Keep generic generation logic separate from clinical rules and interface code.
- Run meaningful checks and report actual results, including failures and checks
  not run.
- Update affected documentation alongside changes. Avoid obvious comments,
  repetitive boilerplate, and speculative abstractions.
- `docs/plan.md` defines scope and acceptance criteria; `docs/progress.json` is
  the authoritative progress record; `docs/decisions.md` records significant
  decisions. Read and update these existing files as relevant.
  `docs/dashboard.html` is a generated, read-only snapshot of progress.json and
  plan criteria; regenerate and commit it alongside changes to either source.
- Local Codex implements changes; the ChatGPT Project handles planning and
  review. Work one reviewable task at a time; the maintainer accepts results.
- Recommend useful skills or plugins when they solve a concrete need. Issues may
  support discussion without creating a duplicate status record.
- Give a concise handoff containing branch/commit, changes, verification,
  blockers, and next action.
- Document runnable setup/check commands when they exist. Do not invent commands
  while application code and tooling are absent.
- Display name: Ravel. Tagline: “Compose the data you need.” Subtitle: “Synthetic
  test data from examples, assumptions and explicit rules.” Intended repository,
  folder, Python import, and CLI names: `ravel`; PyPI name remains unresolved.
- Dashboard commands from the repository root (Python 3.11+, standard library):
  `python scripts/build_dashboard.py`, `python scripts/build_dashboard.py --check`,
  `python -m unittest discover -s tests -v`, and `git diff --check`.
  These checks cover tracking tooling, not application or clinical validation.
