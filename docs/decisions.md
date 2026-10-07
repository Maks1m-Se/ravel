# Decisions

## Agreed

- Clinical and biomedical scenarios come first, with baseline/change from
  baseline in a fictional longitudinal study as the first demonstration.
  First-release boundaries and deferred features remain in [the plan](plan.md).
- Keep the general generation engine separate from clinical rules and thin
  interface adapters. The clinical module initially shares the repository and
  distribution; a public plugin loader/API is deferred.
- Local Codex implements changes; the ChatGPT Project handles planning and
  review. The maintainer accepts changes and release decisions. Work one
  reviewable task at a time.
- [progress.json](progress.json) is the authoritative progress record;
  [plan.md](plan.md) defines scope and acceptance criteria. The dashboard is
  generated from progress.json and plan criteria. Issues support discussion,
  defects, and linked tasks without a duplicate status board.

## Naming decision

- Display name: **Ravel**.
- Repository and folder name: `ravel`.
- Intended Python import and CLI command: `ravel`.
- Tagline: “Compose the data you need.”
- Subtitle: “Synthetic test data from examples, assumptions and explicit rules.”
- Rationale: musical composition/orchestration and examining structure before
  generating controlled data.
- Public PyPI distribution name remains unresolved.
- The naming decision was recorded in `acc430b`, after the planning commit
  `f73dba524838f1c72925b70f13f6ed5153864df3`. At that point branding, local folder
  renaming, and GitHub connection were deferred. The dashboard work applied
  branding and was accepted in `25ed3ae`. The local folder has since moved to
  `C:\Git\ravel`. On 7 October 2026, `main` was fast-forwarded to that accepted
  commit and pushed to the newly created private
  [Maks1m-Se/ravel](https://github.com/Maks1m-Se/ravel) GitHub repository through
  `origin`. Python import and CLI names remain intended; PyPI and license
  choices remain unresolved.

## Dashboard implementation

- Generate a read-only offline HTML snapshot with Python's standard library.
  Progress JSON supplies status, tasks, blockers, evidence, and next action;
  milestone and release-gate tables in the plan supply criterion text.
  Gate thresholds are not copied into generator code or progress JSON.
- Use task-count completion with an explicit size caveat, and show gate
  readiness separately. No schedules, velocity, effort estimates, or completion
  history are inferred. Existing historical planning allowances stay in the plan.
- Regenerate the snapshot alongside source changes. Tracking tools were tested
  with Python 3.11.0 on Windows; the application Python-version choice remains
  unresolved.

## Recipe outline proposed for review

- [The M0-04 specification](specification.md) proposes one JSON-compatible saved
  recipe for the CLI and future Guided/Advanced views, separate recipe schema
  versioning, and an engine/clinical-module/adapter ownership boundary.
- Its invented example checks structure only. Field notation is illustrative;
  schema stability and detailed clinical rules are not adopted by this proposal.
  M0-05 retains clinical edge cases and independent expected results; M2 retains
  selected standards mappings, and M3 retains the detailed sample workflow.

## Unresolved

- Public PyPI distribution name and license (MIT is proposed, subject to
  dependency review).
- Supported Python minor version, locked dependencies, and UI framework.
- Exact platform environments, including macOS version on Apple silicon.
- Installer/signing choices and benchmark reference hardware/frozen workload.
- Detailed recipe schema, selected clinical mapping standard versions, and
  declared handling of ties, missing dose, units, and invalid cases.

Resolve these through the planned specifications and M0 experiments; proposals
are not adopted choices or implementation evidence.
