# Decisions

## Agreed

- The initial plan led with clinical and biomedical scenarios. The maintainer's
  9 October direction below makes both generic entry paths part of the first
  usable release and clinical functionality an optional template. Baseline/change
  in a fictional longitudinal study remains the first clinical demonstration.
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
  sample refinements; the 9 October direction brings the basic sample path into M1.

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

## Generic workbook direction and first M0-06 experiment

- On 9 October 2026, the maintainer approved two first-release entry paths:
  create generic test data from explicit rules, and generate/extend data from
  an imported sample. Both edit one recipe. Generic screens use general terms;
  clinical functionality is an optional domain template. The accepted M0-04
  ownership boundary and M0-05 clinical contracts remain intact. Public add-on
  infrastructure remains later work.
- Basic editable sample assumptions and both output modes now belong in M1,
  before the first usable release; M3 owns deeper sample handling and its full
  criteria. Task IDs, clinical numeric prerequisites and all ten release gates
  are preserved. Planning revision 3 and prior evidence remain historical.
- Evaluate NiceGUI through a small dark graphite scientific workbook with table,
  navigator, properties-panel and toolbar conventions. NiceGUI is a candidate,
  not an adopted framework. This slice uses an invented ten-row CSV, explicitly
  precomputed suggestions and fixed illustrative values, with no production
  profiling, random generation, clinical derivation, installer or plugin loader.
- The experiment uses CPython 3.11 and a pinned Windows environment with NiceGUI
  3.18.0. This is not the final supported application environment. Its
  `ravel-workbook-experiment/1` configuration is provisional and distinct from
  the future application recipe. Numeric bounds here exercise UI validation;
  they do not select clinical representation, rounding or tolerance policies.
- Continue evaluating NiceGUI after the required maintainer UI review. The
  local browser interaction is viable in the tested scope. Remaining obstacles
  are packaging its Python/server/browser dependencies, native file-dialog and
  keyboard review, and clean-machine/cross-platform evidence. This experiment
  does not settle installer/signing or native launch choices. Setup, observed
  checks, screenshots and review steps are in [development.md](development.md#workbook-experiment);
  authoritative status and required action remain in progress.json.

For the initial public snapshot `7f953af`, the maintainer reported a successful range-recovery check on 9 October 2026
and approved the compact light/dark design direction. This is limited feedback,
not acceptance of the complete M0-06 experiment or adoption of NiceGUI. The
published prototype retains its existing dark interface; the proposed themes
and a logo redesign are not implemented in this snapshot. Remaining interaction
and PR source review are recorded in progress.json's next_action.

The subsequent approved M0-06 follow-up implements the compact scientific
workbench and explicit Light/Dark themes, retaining Ravel and the existing R
mark while removing the tagline from the workbook UI. Fixed panes, contextual
help, neutral applied-origin badges and separate draft indicators are the
bounded interface scope. Theme selection is presentation state and must not
modify the provisional configuration, applied origins, drafts, errors or view.
The configuration model, fixtures and clinical contracts remain unchanged.
This implements the approved direction for review; it is not maintainer
acceptance of the complete experiment or NiceGUI adoption. PR #4 stays draft.

The 10 October maintainer report records all seven manual checks passed on the
tested pre-alignment compact-workbench build, including native save/reload and
disconnected operation. Visual alignment remains pending. The supplied approved
HTML governs appearance only; its illustrative data and demo logic do not replace
the application's fixtures or configuration/validation/provenance/draft behavior.
The bounded pass adds local original SVG action icons, applied Settings summaries
and expandable Assumptions, retaining the R mark and repaired contrast. Properties
remains wider than the reference to fit complete errors and origin/draft state.
This is not acceptance of the later aligned build or framework adoption; M0-06
remains partial, NiceGUI provisional and PR #4 draft.

## Proposed M0-06 environment and benchmark (11 October 2026)

**For maintainer review, not adopted.** Keep the tested CPython 3.11.0 Windows
experiment unchanged. Recommend standard GIL-enabled **CPython 3.14** for the
next isolated candidate environment, then pin its current security patch and
platform-specific locks after tests. The [official support table](https://devguide.python.org/versions/)
places 3.14 in bugfix support; [PEP 745](https://peps.python.org/pep-0745/)
specifies regular bugfix releases through **October 2027**, followed by
source-only security releases through **October 2030**. Python 3.13 has
security-only support through October 2029 and 3.11 through October 2027. Python 3.15 has just released;
our PyInstaller 6.20.0 metadata explicitly requires Python `<3.15`. This favors
3.14 over either the old tested interpreter or the newly released minor.

**Compatibility facts when proposed:** installed metadata for all 48 runtime pins, seven build
pins and four review pins permits 3.14 (one shared pin). A Windows x64 `cp314`
wheel-only resolver/download succeeded for all **58 distinct pins** on 11 October,
without installing anything. NiceGUI declares `>=3.10,<4`; PyInstaller declares
`>=3.8,<3.15`. That was metadata/wheel evidence, not an import, runtime or bundle
test on 3.14. The isolated same-host trial below supplies subsequent runtime/build
evidence and records the setuptools import limitation.
Do not reuse the Windows experiment lock as a tested cross-platform release lock.
The original 3.11.0 patch remains historical experiment evidence, not a recommended
security baseline. No interpreter or dependency upgrade is implemented here.

| Proposed target | Architecture and native execution | Available evidence |
| --- | --- | --- |
| Windows 11 Home/Pro **25H2**, build family **26200**, current security update | x86-64; native CPython/bundle | Same-host prototype tested on Home **10.0.26300**, not this proposed clean target |
| Ubuntu Desktop **24.04.5 LTS** | amd64/x86-64; native CPython/bundle | No Ubuntu test environment verified in this work |
| macOS **Tahoe 26.7.1** | arm64 Apple silicon, native; no Rosetta dependency | No Mac hardware/test environment available |
| macOS **Tahoe 26.7.1** | x86-64 Intel on Apple-supported hardware; separate native artifact | No Mac hardware/test environment available |

These are exact proposed starting images, not support claims. Record complete
OS build/patch, browser, interpreter and artifact versions for each future run;
refresh security patches before distributing artifacts. Windows ARM64 and Linux
ARM64 are outside this initial proposal. Microsoft lists [25H2 in support](https://learn.microsoft.com/en-us/lifecycle/products/windows-11-home-and-pro);
Canonical lists [24.04.5](https://ubuntu.com/project/docs/release-team/list-of-releases/)
and [24.04 LTS security maintenance](https://ubuntu.com/security/esm) through May
2029. Apple lists [26.7.1 security updates](https://support.apple.com/en-us/100100)
and [Tahoe-compatible computers](https://support.apple.com/en-us/122867), including
Apple silicon and selected Intel models. Older Intel models are not implied.
Native Apple silicon is a required target, not an emulated Windows substitute.

**UI/distribution recommendation:** continue NiceGUI 3.18.0 as the provisional
candidate for the initial local browser interface, subject to aligned visual
acceptance, native cross-platform checks and the license gaps below. Recommend
per-platform **one-folder console bundles**, local loopback server and an existing
supported browser as the first alpha distribution experiment. The tested Windows
folder is 60.95 MiB with one 2.68-second startup observation, passed both routes,
themes and automated save/reload, and the maintainer passed native JSON and
shutdown checks. This supports continuing the approach, not adopting NiceGUI or
claiming R7. Build natively on each target; do not assume Windows binaries cross-
compile. Defer installer/signing selection until native launch, offline and
redistribution checks; public artifacts still need explicit browser prerequisites,
checksums, notices and macOS signing/notarization/quarantine evaluation. The
[prototype inventory](dependency-licenses.md) records unresolved redistribution
work. No clean-machine or new cross-platform application evidence exists.

**Available reference hardware, queried locally on 11 October:** AMD Ryzen 7
5825U (8 cores/16 logical processors); physical RAM **16,483,872,768 bytes**
(15.35 GiB reported usable physical memory); Windows 11 Home 10.0.26300 x64;
Micron 2210S NVMe 512GB SSD, reported capacity **512,110,190,592 bytes**. Propose
this named laptop as the R6 reference machine, on AC power with Windows Balanced
power mode, local NVMe output and unrelated workloads closed. Record power mode,
free memory/storage, OS patch and versions at measurement time. No benchmark has
run; confirm stable hardware availability before accepting it.

**Proposed frozen R6 workload:** one invented table, exactly **100,000 rows and
20 scalar columns**, ordered `row_id`, `normal_01`?`normal_10`, `flag_01`?`flag_05`,
`integer_01`?`integer_04`. IDs 1?100000 unique/nonmissing; ten independent standard
normal floats, five independent Bernoulli(0.30) booleans and four independent
uniform integers 0?999 inclusive. Missingness zero; no sample/profile, clinical
rules, quotas, linked tables or UI. Fixed seed **20261011**, stable field streams;
freeze recipe/schema/hash and CSV contract before implementation/measurement.
Proposed CSV: UTF-8 without BOM, LF, header in that order, decimal IDs/integers,
booleans `0`/`1`, float round-trip `.17g`, no index. This generic benchmark proposal
does not select clinical arithmetic or export policy.

Run five fresh processes with that same recipe/seed and pinned environment;
time generation plus CSV export from immediately before generation until the
file is flushed and closed, on local SSD (ordinary OS buffering, no forced cache
reset). Exclude process startup, profiling, UI and reports and record those
separately. Verify counts/types/hash for every output. Record all five timings,
CSV sizes, recipe/hash, versions, CPU/RAM/OS/storage and process-tree memory.
Use a process-tree monitor and retain raw samples; supplement simultaneous RSS
with per-process peak working-set counters to expose missed spikes, using the
sum of per-process peaks as a conservative bound until a verified tree-peak
measurement is available. Reject unexplained monitor gaps. **R6 is unchanged:
median elapsed ?60 seconds across five runs and peak process-tree memory ?2 GiB
in every run.** No weaker threshold or benchmark result is proposed. R3/R5 need
their own specified seeds/fixtures; this speed workload does not satisfy them.

## Isolated Python 3.14 trial (11 October 2026)

This follows the proposal above without adopting it or replacing the CPython
3.11 setup. Starting main was `a6abeb97d032f4b0143600b189ac22a6af7bea43`.
The official [Python 3.14.8 release](https://www.python.org/downloads/release/python-3148/)
and Windows downloads list were checked before installation. The x64 installer
matched its published SHA-256 and had a valid Python Software Foundation
Authenticode signature. Standard CPython **3.14.8**, MSC v.1944 AMD64, reports
64 bits, `sys._is_gil_enabled() == True` and `Py_GIL_DISABLED == 0`. Separate
runtime/build/review environments use the existing pins; none is upgraded.

All 18 unit/tracking tests, all three `pip check` runs and eight maintained
runtime browser cases passed. The existing NiceGUI/PyInstaller one-folder recipe
built successfully with **every pin unchanged**, including setuptools 65.5.0.
The copied folder uses its own standard 3.14.8 DLL (byte-identical to the official
installation), app/fixture/import paths within `_internal`, Windows-only PATH and
no Python environment variables. Complete assets match the source. Final bundle
browser results and reproducible commands are recorded in the
[development guide](development.md#isolated-python-314-compatibility-trial).

**Limitation:** a separate `import setuptools` probe fails with
`AttributeError: module 'pkgutil' has no attribute 'ImpImporter'`. PyInstaller also logged a nonfatal `SetuptoolsInfo` probe failure
for that import and continued to build. The passing workbook artifact does not
establish compatibility of setuptools itself. `pip check` checks metadata relationships, not that API.
A setuptools 80.9.0 wheel was downloaded in preparation but **not installed or
used**; no candidate lock or general dependency upgrade is warranted by the
observed pipeline. Do not describe the full build toolchain as compatible merely
because this recipe succeeds. The maintained browser script also emits a
SyntaxWarning for its existing JavaScript `\d` string escape; checks still pass.

**Recommendation for review:** keep Python 3.14 as a viable candidate for this
workbook/runtime and folder-bundle approach, retain the working 3.11 environment,
and decide whether to remove or replace the unused incompatible setuptools pin
in a separately tested candidate build lock before adopting a 3.14 toolchain.
Native clean targets, visual acceptance, workload/benchmark and redistribution
review remain open. This trial does not accept the broader environment proposal,
change release gates or establish other-platform, clean-machine, physical-offline,
native-dialog or redistribution approval. Published UI screenshots still apply.

## Unresolved

- Public PyPI distribution name.
- Supported application Python minor version, release dependency lock and UI
  framework adoption; the experiment-only environment is pinned separately.
- Exact platform environments, including macOS version on Apple silicon.
- Installer/signing choices and benchmark reference hardware/frozen workload.
- Detailed recipe schema, selected clinical mapping standard versions, and
  numeric policies under the recorded M1/M2 prerequisites.

Resolve these remaining choices through the planned specifications and M0
experiments; unresolved proposals are not adopted choices or implementation evidence.
