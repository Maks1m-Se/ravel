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
- Future knowledge files: `docs/plan.md` will hold scope and acceptance criteria;
  `docs/progress.json` will be the authoritative progress record;
  `docs/decisions.md` will hold significant decisions. The future
  `docs/dashboard.html` will be generated from `docs/progress.json`. These files
  do not exist yet; create them only in a task that calls for them.
- Recommend useful skills or plugins when they solve a concrete need. Issues may
  support discussion without creating a duplicate status record.
- Give a concise handoff containing branch/commit, changes, verification,
  blockers, and next action.
- Document runnable setup/check commands when they exist. Do not invent commands
  while application code and tooling are absent.
