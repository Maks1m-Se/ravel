# Ravel — project plan

Planning revision 3 · 6 October 2026 · Target release v0.1 · Display name: Ravel

**Compose the data you need.**

Synthetic test data from examples, assumptions and explicit rules.

Repository and folder names: `ravel`; intended Python import and CLI names:
`ravel`. Repository: [Maks1m-Se/ravel](https://github.com/Maks1m-Se/ravel).
Public PyPI distribution name remains unresolved.

Build a free, open-source, offline application for creating clinical test scenarios with verifiable expected results. Keep a general data-generation engine underneath it. The first demonstration is baseline and change from baseline in a fictional longitudinal study.

This document defines proposed release criteria. Nothing here is a claim that software, benchmarks, user tests, or clinical validation already exist.

**Working setup.** Local Codex implements changes, runs checks, and investigates failures. The ChatGPT Project handles planning and review; the maintainer accepts changes and release decisions. Keep code, specifications, evidence, and durable decisions in the repository rather than depending on chat history. `docs/plan.md` defines scope and acceptance criteria; `docs/progress.json` is the authoritative status record. The read-only `docs/dashboard.html` is generated from that record and the criterion tables here; regenerate it alongside source changes using `python scripts/build_dashboard.py`. Record significant decisions in `docs/decisions.md` when useful. A ChatGPT Project and a Codex working directory are distinct.[1–3]

Work one reviewable task at a time. GitHub Issues may hold discussions, bug reports, and linked implementation tasks; avoid a separately maintained status board. Track milestone and task status in `docs/progress.json`. A separate website can wait; the README and a working release are the first public presentation.

**First-release boundaries.**

| Include in v0.1 | Schedule after v0.1 |
| --- | --- |
| Generation from explicit specifications and saved recipes | Natural-language generation and local language models |
| Single-table sample profiling, editable assumptions, and generation | Automatic fitting of arbitrary linked clinical datasets |
| Generated-only output or retain-and-extend output | Formal privacy guarantees or differential privacy |
| Linked subject, exposure, and biomarker records for one clinical template | Additional clinical domains, survival scenarios, preclinical templates |
| Twelve baseline/change scenarios with reference results | Broad CDISC coverage, Define-XML, SEND, submission packages |
| A command-line interface and a local browser interface | Hosted services and user accounts; mobile is outside the intended scope |
| Guided and Advanced views of the same recipe; separate clinical domain module | Community recipe packs, then a documented Python extension interface when needed |
| CSV datasets, JSON recipes, data dictionary, validation report | Parquet and SAS/XPT adapters unless a concrete early use requires them |
| Tested Windows 11 x64, Ubuntu 24.04 LTS x64, and macOS on Apple silicon | Additional OS versions, Linux distributions, and Intel Macs after dedicated testing |

Generated-only means source records are not appended. It does not promise every generated row is different from every source row. Uniqueness is an explicit constraint; impossible requests fail clearly. Retain-and-extend preserves the imported values and marks row origin. The interface distinguishes “generate N new records” from “extend to N total records.”

For sample-assisted generation, infer types, missingness, categories, and simple marginal parameters. Show these as editable estimates. Exclude identifier fields from fitting by default. Let users declare new categories, ranges, missingness, quotas, and supported dependencies. Do not imply that independently fitted columns preserve associations. Ten source observations provide a starting specification, not evidence about an entire population.

The clinical template generates underlying study records first and derives analysis outputs from those records. It expands subjects together with their dependent records. Supported mappings will list selected variables from DM, EX, LB, ADSL, and ADLB, with exact standard versions and limitations. These mappings do not establish whole-dataset or submission conformance.

**Implementation approach.** Build one Python package with a general engine, recipe validation, a bundled clinical domain module, exporters, and thin CLI/UI adapters. The engine handles entities, fields, relationships, distributions, and constraints; subject, dose, and baseline semantics belong in the clinical module. Keep generation rules out of interface code. Use an R reference workflow for independently checking baseline and change derivations. A SAS companion is useful when it can be executed in a licensed environment; unexecuted SAS code must be labelled accordingly and is not a release gate.

At kickoff, fix one supported Python minor version and lock the development/release environment. Choose the UI framework through a small offline launch, keyboard-use, and packaging experiment. Choose dependencies for demonstrated needs. The application itself must run without Codex, an AI account, or an internet connection. Development with cloud AI uses invented fixtures; confidential samples stay outside the repository and AI context.

**Platform scope.** macOS, Linux, and Windows are intended desktop targets. Fix exact OS versions and architectures at M0, including at least one macOS version on Apple silicon. Add automated core checks on all three as the engine becomes runnable, then test native installation and the actual interface separately. Publish only tested combinations as supported. The alpha may identify platform gaps; v0.1 requires all three selected targets. A browser interface runs locally and does not imply a hosted service.

**Community add-ons.** Preserve a small boundary between core generation and domain rules now. Keep the clinical module in the same repository and distribution initially. Avoid a plugin loader, registry, or public API stability promise before real extension needs are understood.

| Stage | Extension capability | Completion evidence |
| --- | --- | --- |
| v0.1 | Clinical logic uses explicit internal interfaces; recipes have a schema version | Clinical-specific assumptions remain outside the general engine; existing release gates pass |
| After v0.1 | Import/export domain recipe packs with metadata and examples | A small contributed finance or engineering example runs through the existing engine without changes to core code |
| When recipes are insufficient | Optional Python packages for new generators, validators, or exporters | One external domain pack works against the documented interface; compatible versions load and incompatible versions fail clearly |

Recipe packs are declarative and validated; importing them must not execute arbitrary Python, SQL, or expressions. A pack should identify its author, license, version, compatible engine/schema versions, assumptions, and a runnable example with expected checks. Record the exact pack version in each run. Domain authors remain responsible for the assumptions in their examples; listing a pack is not clinical or financial validation.

Python packaging already provides entry points for discovering installed extensions, so a future loader can use that standard mechanism.[5] Executable extensions run code with the application's permissions; enable them explicitly from trusted packages, including offline installation. Do not describe them as sandboxed. Community contributions can begin earlier with cases, recipes, bug reports, documentation, and platform testing.

**Milestones.** Each milestone produces something runnable or reviewable. Testing accompanies implementation throughout.

| Milestone | Deliverable | Exit condition |
| --- | --- | --- |
| M0 — Foundation | Repository scaffold, recipe outline, concise contributor/release rules, baseline specification, packaging/UI experiment | A fresh checkout can run a meaningful smoke test; Windows/Linux/macOS target environments and the core/domain boundary are recorded; three tiny baseline cases are reviewed |
| M1 — Working slice | CLI generates 10 subjects, exposure records, and one biomarker over baseline plus four scheduled follow-up visits | One command produces linked CSV files, recipe, dictionary, and validation result; repeat runs reproduce content; impossible requests produce actionable errors |
| M2 — Clinical alpha | Twelve clinical cases, selected source-to-analysis mappings, independent R checks, one example table and figure | Every expected result agrees; three deliberately incorrect derivations are detected; a tagged public alpha can be reproduced from its quickstart |
| M3 — Sample workflow | Profile an invented CSV, edit assumptions, generate-only or retain-and-extend | A 10-row sample yields exactly 1,000 new rows or exactly 1,000 total rows as selected; retained records and row origin are verified; explicit new categories appear as requested |
| M4 — User interface | Guided flow, Advanced controls, recipe preview/save/reload | Both views use the same engine and preserve all settings on switching; keyboard operation and invalid-input recovery work through the full workflow |
| M5 — Distribution | Windows/Linux/macOS installation paths, offline bundles, benchmark and release checks | Clean-machine installation and offline generation pass on all three targets; performance and reproducibility gates pass; update/reinstall instructions pass a smoke test |
| M6 — v0.1 | Usability fixes, concise documentation, release artifacts, demonstrated limitations | All release gates below have evidence; no unresolved release-blocking defects; five-person usability exercise meets its target |

Publish the alpha after M2, once its license, installation instructions, limitations, and checks are ready. Keep its scope clear. Full v0.1 adds the original sample-expansion workflow and accessible UI.

Initial planning allowance from revision 1: roughly 120–180 focused hours, including review, learning, documentation, and packaging. At eight hours per week that is about 15–23 weeks. Adding native macOS validation introduces work not yet estimated; review the budget after the M0 packaging experiment and M1 implementation. Public add-on infrastructure is outside this v0.1 budget. Publish the alpha and use its demonstrated work in applications before the entire plan is finished.

**Clinical specification.** The first rule is: select the last nonmissing biomarker measurement strictly before the first actual dose, within subject and parameter. Calculate change as follow-up value minus baseline in compatible units. Absence of an eligible baseline produces a missing baseline and change with an explicit reason. Ties require a declared rule or a clear error. This is the example project's rule, not a universal clinical convention.

The twelve reference cases cover: ordinary baseline; multiple eligible measurements; latest pre-dose value missing; no eligible baseline; an observation exactly at first dose; a post-dose observation labelled baseline; duplicate eligible timestamps; out-of-order input; missing actual dose; incompatible units; no usable measurements; and multiple subjects/parameters requiring correct grouping. Fix each expected result by hand before implementing the derivation. Mark intentionally invalid cases separately from valid unusual cases.

**v0.1 release gates.** Store evidence against the release commit in a short validation report. Failures block the v0.1 label; an honestly scoped alpha can remain public.

| ID | Pass criterion | Evidence |
| --- | --- | --- |
| R1 — Clinical correctness | All 12 reference cases match their specified results, including expected errors. Tests reject at least three wrong derivations: inclusive dose boundary, selecting a missing latest value, and grouping across subjects | Reviewed fixtures, R comparison, targeted mutation results |
| R2 — Counts and integrity | Every accepted reference recipe produces the exact requested counts and quotas, valid keys, supported types, and required temporal relations. Zero unexplained rule violations; deliberate defects match the scenario manifest. No silent rule relaxation or successful partial output | Automated checks, including infeasible recipes |
| R3 — Reproducibility | For each of five fixed seeds, three runs with the same recipe, input, application version, and pinned environment have identical canonical dataset hashes. Adding an independent field leaves existing fields unchanged | Hash comparison; stable entity/field random streams; OS-specific evidence |
| R4 — Sample handling | Both 10-to-1,000 workflows pass; retain-and-extend preserves all imported cell values and marks originals; generated-only appends none. Unsupported fields and overrides are reported. Requested new categories and exact quotas are respected | End-to-end invented sample fixtures |
| R5 — Statistical behaviour | For five preselected seeds and n=100,000: a standard-normal fixture has absolute mean ≤0.02 and SD between 0.98 and 1.02; a Bernoulli(0.30) fixture has proportion between 0.29 and 0.31; a Gaussian-pair fixture targeting correlation 0.60 has observed correlation between 0.57 and 0.63 | Repeatable statistical checks; these test known generation rules, not real-world fidelity |
| R6 — Speed and memory | Generate and export a fixed 100,000-row × 20-scalar-column recipe to CSV with median elapsed time ≤60 seconds over five runs and peak process-tree memory ≤2 GiB in every run | Named reference machine, CPU/RAM/OS/storage, versions, recipe, and raw timings recorded; startup, profiling, UI, and reports measured separately |
| R7 — Offline and installation | Install from a prepared offline bundle and complete both principal workflows with external networking blocked on clean Windows, Ubuntu, and macOS targets. No application-originated external requests; localhost communication allowed. Bundle includes dependencies; OS/browser and any interpreter prerequisites are explicit | Clean-machine checklist, application network observations, bundle checksums |
| R8 — Usability | At least 4 of 5 first-time testers complete each task without coaching within 10 minutes after installation: generate/export a specified clinical scenario; import an invented sample, change a category setting, and export a requested count | Task sheet, timing, completion and errors; include clinical and general users |
| R9 — Interface consistency | Switching Guided/Advanced or saving/reloading preserves the canonical recipe. Both workflows are keyboard-completable with labelled controls and readable error messages | Automated state checks and manual interaction review |
| R10 — Release evidence | Core checks pass on all three supported OS targets. No known silent incorrect output, data loss, unintended disclosure, or blocked core workflow remains. Quickstart succeeds from a clean checkout. License and dependency notices are present. Each release has a tag, notes, artifacts/checksums, and tested update instructions | CI results, release checklist, issue review, artifact links |

For R3, byte equality applies inside each pinned environment. Cross-platform reference results use declared numeric tolerances; do not promise arbitrary bitwise identity across operating systems or future dependency versions. Canonical hashes exclude timestamps and other changing run metadata.

For R6, choose and record the reference hardware at M0. Freeze the workload before measuring it. Do not quietly weaken the threshold after a failed benchmark.

Every output includes its recipe/version/seed, dictionary, checks, and whether source records were retained. Input-derived recipes and reports may themselves be sensitive. Privacy status defaults to “not assessed.” An offline run and a source-overlap check are not anonymisation certification. Public examples use invented records.

**Release and update policy.** Keep the process small and repeatable. Start with versioned alpha releases, then 0.1.0. During 0.x, use patch releases for compatible fixes and minor releases for features or deliberate breaking changes, documenting the latter prominently. This is our stated pre-1.0 policy; SemVer itself treats 0.x APIs as unstable. Adopt normal major/minor/patch compatibility rules once the public API is stable at 1.0.[6]

Use short branches and focused pull requests into a working main branch. Automated checks run before merging. Tag a tested commit, build its artifacts, and publish concise GitHub release notes covering changes, fixes, limitations, supported platforms, and migration steps. GitHub Releases supports distributing notes and binary assets alongside a tag.[7] Keep released artifacts unchanged; publish a new version for corrections. Maintain one canonical release history.

Version the recipe schema separately from the application. Record application, dependency environment, seed, schema, and domain-pack versions for each run. Any change that can alter generated values, distributions, constraints, or clinical derivations must be identified in release notes, including bug fixes. Reproducibility applies to the recorded environment, not automatically across upgrades. Reject unsupported recipes clearly; migrations create a reviewed new copy rather than silently overwriting the original.

Updates are manual and offline-capable initially. No automatic downloads, update checks, or forced migrations. Retain access to previous releases and document reinstallation; identify versions with known correctness or security defects. Before v0.1, test upgrading from the preceding alpha and confirm a saved supported recipe still loads or receives a clear migration/error message. Pin release environments and review dependency updates in focused pull requests with relevant regression checks. Native installer/signing choices are evaluated at M0 and described honestly in installation instructions.

You remain the maintainer who accepts changes. Welcome outside contributions through a short contributing guide, a minimal bug-report template, reproducible invented examples, and a few bounded starter issues. Add further process when actual maintenance needs justify it.

**How we work together.** The maintainer owns the intended behaviour, clinical assumptions, acceptance of results, and release decisions. The ChatGPT Project handles planning and review. Local Codex implements the agreed task, runs checks, investigates failures, and explains the relevant code. At each milestone the maintainer should be able to explain the underlying rule, an edge case, and how its correctness was checked.

Use the following loop:

1. Define one reviewable task with the user problem, included scope, and observable acceptance criteria in the repository documents. Link a GitHub Issue when useful for discussion or implementation detail.
2. For statistical behaviour, agree a small input and independently established expected output before coding.
3. Local Codex implements on a focused branch. Keep changes limited to that task and add meaningful regression checks.
4. Review the diff and test evidence in the ChatGPT Project and repository. A separate AI review can help find problems, but does not establish independent clinical validation.
5. Run the example yourself, review the domain logic, then accept the change. Use a pull request to retain the decision and evidence.
6. Update affected documentation and task/milestone status in `docs/progress.json`. Record significant decisions in `docs/decisions.md` when useful. End with branch/commit, changes, actual verification results, blockers, and the next action.

Tasks should normally fit a one-to-three-hour reviewable unit. Split work by behaviour, not arbitrary file count. Discuss scope, clinical-rule, interface-contract, license, and dependency changes when they affect the agreed design. Routine implementation details can proceed autonomously.

At the end of each working week, check one runnable example when one exists, the open blockers, and the next tasks. Keep durable decisions in specifications and `docs/decisions.md`, with issue links when useful. `docs/progress.json` remains the sole maintained status record; regenerate the dashboard alongside changes to it or the plan. Avoid duplicate status documents and chat transcripts in the repository.

**Repository documentation.** Add each document when it has useful content.

| File or location | Contents |
| --- | --- |
| README.md | Purpose, actual supported workflows, quickstart, one screenshot/example, limitations, and brief AI disclosure |
| [LICENSE](../LICENSE) | Approved MIT license; dependency/license review remains required before public alpha |
| CONTRIBUTING.md | Setup/check commands, issue/PR expectations, and responsibility for AI-assisted contributions |
| AGENTS.md | Short repository instructions for coding agents; aim for roughly 30–50 useful lines |
| docs/specification.md | Recipe behaviour, clinical rules, supported mappings/versions, units, date/tie handling |
| docs/validation.md | Release criteria, reproducible verification commands, results and limitations |
| SECURITY.md and CODE_OF_CONDUCT.md | Real reporting/contact routes and concise community expectations, before inviting contributions |
| examples/ and tests/ | Runnable invented examples and small reviewed reference fixtures |
| docs/plan.md | Maintained scope, milestones, acceptance criteria, and release gates (planning revision 3) |
| docs/progress.json | Authoritative milestone/task status, evidence, blockers, and next action |
| docs/decisions.md | Significant agreed decisions and visibly unresolved choices |
| [docs/development.md](development.md) | Dashboard usage, maintenance, verification commands and contributor/release preparation |
| docs/dashboard.html | Generated offline snapshot of progress.json and plan criteria; rebuild with `python scripts/build_dashboard.py` |
| GitHub Issues and releases | Discussions, bug reports, linked implementation tasks, release changes and downloads; no duplicate status board |

GitHub recognises contributor guidance, security policies, codes of conduct, and issue/PR templates as normal community documentation.[4] These should provide usable instructions; empty policy files and aspirational features add no value. A dedicated changelog can be added when release history needs one; avoid maintaining duplicate change lists.

Use descriptive names and short public API docstrings. Comments explain clinical assumptions, statistical choices, units, numerical issues, or non-obvious constraints. Avoid narrating obvious code, decorative banners, repeated generated headers, speculative abstractions, and large prompt dumps. Tests should catch wrong behaviour rather than reproduce implementation line by line. Coverage percentages and code volume are not release goals.

Suggested README disclosure, once this workflow is in use:

> This project is developed with AI coding assistants. The maintainer defines the clinical and statistical specifications, reviews changes, and is responsible for testing and releases. Validation evidence and known limitations are documented.

Describe the project publicly as AI-assisted development. If asked about vibe coding, explain exactly how you use it and show the reviewed specifications and evidence. Do not claim external validation, productive clinical deployment, or standards compliance beyond what was demonstrated.

**First working session (original planning direction).** The temporary working title has since been settled as Ravel. Establish the repository, concise AGENTS.md, and M0–M6 tracking in `docs/progress.json`. Document installation/check commands when runnable tooling exists; establish the first three hand-checkable baseline fixtures. Complete the M0 specifications and experiments before the first M1 CLI implementation task. The rest of the application grows from that working example.

References checked on 6 October 2026:

1. [OpenAI: Projects and chats](https://learn.chatgpt.com/docs/projects)
2. [OpenAI: Codex IDE extension](https://learn.chatgpt.com/docs/codex/ide)
3. [OpenAI: Custom instructions with AGENTS.md](https://learn.chatgpt.com/docs/agent-configuration/agents-md)
4. [GitHub: Community health files](https://docs.github.com/en/communities/setting-up-your-project-for-healthy-contributions/creating-a-default-community-health-file)
5. [Python Packaging User Guide: Creating and discovering plugins](https://packaging.python.org/en/latest/guides/creating-and-discovering-plugins/)
6. [Semantic Versioning 2.0.0](https://semver.org/)
7. [GitHub: About releases](https://docs.github.com/en/repositories/releasing-projects-on-github/about-releases)
