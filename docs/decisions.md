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
- The naming decision was recorded in `506c944`, after the planning commit
  `69effadff49540da5002326ecac6dbfe35d2b3cd`. At that point branding, local folder
  renaming, and GitHub connection were deferred. The dashboard work applied
  branding and was accepted in `9f61694`. The local folder was renamed `ravel`.
  On 7 October 2026, `main` was fast-forwarded to that accepted commit and pushed
  to the newly created
  [Maks1m-Se/ravel](https://github.com/Maks1m-Se/ravel) GitHub repository through
  `origin`. Python import and CLI names remain intended. At connection time,
  PyPI and license choices remained unresolved; MIT adoption below records the
  later license decision.

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
- Show explicit current focus before branding and overall counts. Progress JSON
  stores only `current_task_id` and ordered `next_task_ids` (up to two); the
  dashboard derives record details and reuses `next_action`. Advance focus with
  accepted-task status updates rather than inferring priority from IDs or status.

## Accepted recipe architecture

- Hub review of `7ee3252` accepted [the M0-04 architectural outline](specification.md):
  one JSON-compatible saved
  recipe for the CLI and future Guided/Advanced views, separate recipe schema
  versioning, and an engine/clinical-module/adapter ownership boundary.
- Its invented example checks structure only. Field notation is illustrative;
  schema stability remains unresolved. Explicit generic/clinical routing and
  stable seed/entity/field random streams were
  confirmed; clinical-looking names cannot activate clinical rules.
  M0-05 records the accepted fictional clinical policies and four reference
  cases; M2 retains selected standards mappings, and M3 retains the detailed
  sample workflow.

## Accepted fictional clinical specification

- [The M0-05 baseline specification](baseline-specification.md) preserves the plan's
  last-nonmissing, strictly pre-dose rule and provides four hand-worked cases
  within the existing twelve planned scenarios.
  Actual-dose recognition, timestamp precision/timezones, tie errors, exact
  units without conversion, post-dose targets, missing-result reasons and
  whole-run errors were accepted by the maintainer on 8 October 2026, together
  with the validation/output contracts and four cases, as a fictional test-data
  specification. Acceptance does not establish standards conformity, implemented
  functionality or independent clinical validation.
- The Hub's final document review is recorded separately from the earlier
  Claude reviews in progress.json. Claude's earlier findings informed revisions;
  no final-revision review by Claude is asserted.
- The maintainer-supplied external AI review prompted explicit negative-fixture
  versus derivation contracts, group/change/record-diagnostic outputs, an extra
  boundary illustration and versioned CDISC/FDA source context. The specification
  retains strict pre-dose selection as the fictional study rule and distinguishes
  it from scoped software restrictions; no universal clinical or submission
  compliance is claimed. AI review does not establish independent clinical
  validation. Historical preparation evidence remains in progress.json.
- Follow-up review, including Claude's crossed-pair counterexample, prompted
  explicit declared subject/parameter membership and deterministic validation
  dependencies. Failed dose records block their subject's anchor; failed
  measurements block their declared group's baseline selection without fallback.
  The specification distinguishes evaluable failures, failed-prerequisite skips and
  valid missing reasons; manifests match failures by code/scope/source IDs.
  Independent checks continue and whole-run output suppression remains intact.
- Arithmetic representation/range, rounding, export formatting and Python/R
  comparison tolerances remain unresolved. Specify these before M1-01 clinical
  numeric implementation and align M2-02 R comparison with the plan's R3
  qualification. No mandatory decimal-scale recipe attribute is selected.
  Existing task criteria now record that prerequisite, M2-01's ownership of
  specified clinical outputs/negative fixtures with expectations before their
  derivations, and M2-02's tolerance documentation. M1 scope is unchanged.
- Maintainer review of critical clinical decisions and important user-facing
  behavior is required before acceptance. Required action remains in
  progress.json's next_action; runnable additions supply exact review/try-out
  steps and expected outcomes. No runnable clinical functionality exists yet.

## Email privacy cleanup and publication

- On 8 October 2026, the maintainer authorized rewriting personal email
  metadata while preserving author names, original dates, commit ancestry,
  accepted work and unrelated content. Repository commits now use the verified
  GitHub noreply identity. The reviewed local M0-05 preparation was committed
  before the rewrite; M0-05 remains accepted.
- Current commit references point to rewritten equivalents. Historical evidence
  descriptions retain their original scope and limitations; the old-to-new
  mapping and recoverable original history are kept privately outside the
  repository, with no active push remote on the archives. Invalidated GitHub
  signatures were removed by the rewrite.
- Clean branch history does not prove removal from GitHub PR references or
  cached commit views. Publication was initially blocked while retained history
  remained accessible; the original findings and limitations remain in progress
  evidence E16 and E17. Complete erasure has not occurred.
- On 8 October 2026, the maintainer explicitly accepted that the personal email
  remains discoverable in GitHub's retained historical commits. The active
  privacy publication blocker is removed because the exposure is accepted,
  not because the email was completely removed. Keep the existing repository
  and cleaned history, and continue using the verified GitHub noreply identity
  for future commits. No further history cleanup, migration or Support request
  is required.
- The maintainer authorized updating and merging PR #3 while preserving its
  commits, then making the existing repository public after checks pass, as an
  early development preview. This is not an alpha or v0.1 release and establishes
  no application functionality, standards conformity or clinical validation.
  M0-06 and M0-07 remain pending; all release gates remain unverified.

## Visitor documentation and MIT licensing

- On 8 October 2026, the approved [MIT license](../LICENSE) was added with
  copyright 2026 Maksim Sendetski. No further license-choice decision is needed;
  earlier license proposals are historical. Dependency/license review and
  remaining contributor/release rules are still M0-07 work.
- The [README](../README.md) introduces the intended audience, current status,
  four accepted specification reference cases and planned capabilities and
  architecture. Dashboard usage, maintenance and check commands live in the
  [development guide](development.md). The examples make no claim of executed
  generation, personal authorship of every calculation or independent clinical
  validation. Planned reproducibility includes recipe, input, seed, application
  version and pinned environment.
- Documentation/license preparation did not complete M0-07, change accepted
  clinical contracts or numeric prerequisites, establish a release gate, or
  clear the retained-history publication blocker at that time. PR #3's then-
  outdated description required updating before merge. The later maintainer
  decision above accepts the residual exposure and authorizes publication.

## Unresolved

- Public PyPI distribution name.
- Supported Python minor version, locked dependencies, and UI framework.
- Exact platform environments, including macOS version on Apple silicon.
- Installer/signing choices and benchmark reference hardware/frozen workload.
- Detailed recipe schema, selected clinical mapping standard versions, and
  numeric policies under the recorded M1/M2 prerequisites.

Resolve these remaining choices through the planned specifications and M0
experiments; unresolved proposals are not adopted choices or implementation evidence.
