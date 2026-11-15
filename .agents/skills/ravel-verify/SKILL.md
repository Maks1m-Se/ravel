---
name: ravel-verify
description: Verify a Ravel repository change using its existing checks, invented references and actual running UI. Use for Ravel implementation or review; not for unrelated applications or clinical acceptance.
---

# Ravel verification

Read the repository instructions and the affected specification before selecting
checks. Start from `git status --short`, `git diff --stat` and the actual diff;
include untracked implementation and fixtures. Preserve existing work and
valid evidence. Use `docs/progress.json` for status and `docs/plan.md` for gates;
this skill does not define publishing policy or accept a milestone.

Use the configured source interpreter described in `docs/development.md`.
Run the existing commands from the repository root:

- Core/schema/session/CLI changes: `python -m unittest discover -s tests -v`.
  Begin with an affected `-p test_*.py` pattern when diagnosing a failure.
  Check hand-established fixture results and atomic failure/reproducibility,
  rather than deriving expected data with the implementation under test.
- Progress/plan changes: `python scripts/build_dashboard.py`, then
  `python scripts/build_dashboard.py --check`. Do not hand-edit dashboard HTML.
- Every reviewable package: `git diff --check`.
- UI, sample or layout changes: run the real app on a dedicated development
  port, then `python scripts/check_generator_browser.py --base-url URL
  --workflow all --output outputs/browser-review`. Use the full Light/Dark
  laptop matrix; `--channel msedge --smoke` provides a separate host Edge smoke
  check when Edge is installed. Never target a frozen manual-review instance.
  `--workflow rules` or `sample` selects focused diagnosis. Reuse valid checks
  on unchanged code; rerun the affected coverage after a meaningful fix.
- Packaging changes: read the current build/notice/checklist instructions in
  `docs/development.md` and the affected packaging specification. Validate the
  actual candidate; mocked build checks and a source server are insufficient.

Inspect the actual captured interface: source/result distinction, readable
errors, stale export, keyboard focus, both themes and short laptop height.
Wait for visible current Preview and its expected row count before capture.
Keep Fichte colors and Properties resize/ARIA/window-restore regressions.
Run any optional interactive browser skill when available and useful; its
absence does not replace or block the maintained Python checks.

Record the tested branch/commit or snapshot/source hashes, actual command
results and Python/framework/browser versions. Retain failed runs separately.
State unrun checks and external blockers precisely; browser network interception,
development-host execution and hosted CI do not prove disconnected clean-machine
installation. Keep human acceptance attributed to its exact tested version.
Update affected specifications, progress and dashboard, then give a concise
review handoff with the runnable steps and remaining limitations.
