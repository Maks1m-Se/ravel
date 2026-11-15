# Development guide

Runnable source now includes an explicit-rule single-table engine, CLI and
NiceGUI table builder, alongside the tracking dashboard and historical workbook
experiment. Sample profiling, linked/clinical generation and binary distribution
remain outside this increment. The provisional source recipe is specified in
[single-table.md](single-table.md); it is not the old experiment configuration.

## Single-table source development

Use **standard CPython 3.14.8 x64 with the GIL enabled** for this source preview.
The [selection rationale](decisions.md#staged-single-table-source-increment-15-october-2026)
uses the recorded candidate evidence, current official information and a newly
isolated source environment. The headless core has no third-party dependencies.
The UI retains the established 48 runtime pins in `requirements-ui.lock`, and
browser tools remain separate in `requirements-review.lock`. Binary build locks,
including the setuptools 80.9.0 candidate, are not selected or invoked here.

From the checkout root in PowerShell:

```powershell
py -3.14 -m venv .venv-source
.\.venv-source\Scripts\python.exe --version
.\.venv-source\Scripts\python.exe -m pip install -r requirements-ui.lock
.\.venv-source\Scripts\python.exe -m pip check
.\.venv-source\Scripts\python.exe -m ravel ui
```

The version must be **3.14.8**. Open **http://127.0.0.1:8090/**; stop with Ctrl+C.
The source server binds loopback, serves assets locally and does not open a
browser automatically. Port 8090 must be free. The separate `.venv-source`
preserves earlier experiment environments. Installation needs network access;
subsequent source use requires no AI service. Page state is session-only.

Core/CLI use from the same checkout, without installing UI dependencies:

```powershell
New-Item -ItemType Directory -Force outputs/tryout
.\.venv-source\Scripts\python.exe -m ravel validate examples/three-rows.recipe.json
.\.venv-source\Scripts\python.exe -m ravel generate examples/three-rows.recipe.json --csv outputs/tryout/reference.csv
```

The three expected rows were established before coding: `(1, demo, 10)`,
`(2, demo, 12)`, `(3, demo, 14)`. The CLI writes all-quoted UTF-8/LF CSV, a
canonical recipe sidecar and a run sidecar with environment and checksums.
It rejects colliding/existing output paths and does not overwrite the input.
Use a new CSV filename on repeat runs. On validation or ordinary I/O failure it
reports an error and removes only files it created during that failed write.
This is not a crash-atomic multi-file filesystem transaction.

The builder separates applied recipe, explicit drafts and immutable generated
result. Apply commits table and selected-column edits atomically; selecting,
adding, duplicating, generating or saving requires applied/discarded drafts.
Changes mark previous data **Out of date**; CSV/run export requires a current
matching result without drafts. Preview and CSV use the same cell serializer.
Loading a valid recipe resets the layout and clears results; invalid and old
experiment JSON preserves the current table/drafts/result. Old JSON is rejected
with an explicit explanation rather than migrated; the uploaded original is read
only. Native chooser interaction remains a separate manual check.

### Maintained single-table checks

```powershell
.\.venv-source\Scripts\python.exe -m unittest discover -s tests -v
.\.venv-source\Scripts\python.exe scripts/build_dashboard.py
.\.venv-source\Scripts\python.exe scripts/build_dashboard.py --check
git diff --check
.\.venv-source\Scripts\python.exe -m pip install -r requirements-review.lock
.\.venv-source\Scripts\python.exe scripts/check_generator_browser.py --output outputs/generator-browser-review
```

Start the source server in another terminal before running the browser command.
Use a fresh output directory for each run. Installed Chrome is used by default;
no browser download is required. Browser HTTP/WebSocket non-loopback destinations
are blocked by the harness. This is distinct from server socket guards, OS-level
disconnection, native installation and clean-machine evidence.

The read-only [core workflow](../.github/workflows/core.yml) runs standard-library
tests, dashboard freshness and whitespace on hosted Windows/Linux/macOS Python
3.14.8 jobs. Its remote results remain pending until publication and execution;
the workflow is not native UI/installation testing or support certification.

### Short maintainer walkthrough

The walkthrough is retained for reproducibility; E46 records the maintainer's
current-app acceptance, and joint code review remains required. At 1366×657 and
1280×800 in Light/Dark:

1. Launch the source UI, choose **Create table**, then **Generate table**. Expect
   1,000 actual rows, a first-100-row preview, current status and enabled CSV
   export. Export CSV, save recipe and save run record. The run record includes
   the exact recipe, environment and CSV checksum.
2. In Fields, select `value`, enter Maximum `20` and Minimum `200`, then Apply.
   Expect a focused inline range error, retained drafts and blocked generation/
   save until Apply or Discard. The previous preview stays visible as out of
   date and CSV export is disabled. Correct Minimum to `5`, Apply, then Generate.
3. Add a column, rename it, choose a rule and configure it. Category input uses
   CSV lines `A,0.25` and `B,0.75`; missingness is a probability 0–1, not a quota.
   Duplicate a random column and inspect its separately saved identity. Remove
   it once with Cancel and once with confirmation. Expect clear draft/stale state.
4. With an unfinished edit, widen Properties to 560 using End, narrow to 900 px,
   then restore: expect 560 → 446 → 560 and unchanged edits. Try Escape during
   drag, constrained Reset, themes and Fields/Preview. Save a valid recipe,
   change the table/layout and reload via the native chooser: expect the saved
   rules, default 312 px preference and no result until Generate. The regenerated
   CSV must agree with the earlier saved recipe's output.
5. Open `examples/three-rows.recipe.json`, Generate and compare the three rows
   above. Try old workbook JSON: expect an explicit rejection and preserved state.
   Run the headless example and compare UI/CLI output for the same saved recipe.

These steps review new user-facing behaviour; they do not accept clinical rules,
NiceGUI adoption, native distribution or the full M1 milestone. Sample import/
profiling follows next, then linked tables; both entry paths remain required
before the first usable release. M0 packaging/platform work stays open.

Actual captures from the source app (invented data):
[Dark fields](images/m1-single-table-fields-dark.png),
[Light generated preview](images/m1-single-table-generated-light.png),
[Light validation](images/m1-single-table-error-light.png), and
[Dark start screen](images/m1-single-table-start-dark.png).

The historical sections below retain their original evidence and limits.

### Single-table verification record (16 October 2026)

The selected source environment was recreated in an isolated venv from prepared
cp314 wheels without contacting an index. Standard CPython **3.14.8 x64**, GIL
enabled, all **48 UI + four review pins**, imports and `pip check` passed. No build
lock or binary build was used. The recorded source command from the feature
worktree used the original checkout's
`outputs/single-table-2026-10-15/source-env/Scripts/python.exe`.

- **41 unit tests passed:** 13 engine/CLI, six session-state, nine existing
  configuration, nine tracking and four mocked packaging-recipe tests. The core
  checks hand arithmetic and independently derived types/bounds/categories and
  probability properties; it does not use its own random output as the reference.
  Local decimal context isolation and literal CR/LF/quotes/Unicode CSV round trips
  are covered. Mocked build tests do not create a new bundle.
- **Final maintained browser run: four cases passed** at 1366×657 / 1280×800 in
  Light/Dark on Windows 11 build 26300, NiceGUI 3.18.0, Playwright 1.58.0 and
  Chrome **155.0.8059.82**. It checks 1,000 rows, all rule editors including ID
  starts/negative sequence steps, add/duplicate/rename/remove, actual preview/CSV/
  core agreement, recipe repeatability and run records, invalid/stale protection,
  start-screen recipe opening, contextual help, Home theme preservation and the
  accepted Properties/viewport/ARIA/cancellation/reset/theme/view regressions.
  Browser non-loopback HTTP/WebSocket attempts and page errors were **zero**.
- Measured text minima: Light **6.14:1**, Dark **6.99:1**; divider focus
  **5.52:1 / 6.83:1**. Unchanged accepted Fichte token/control-boundary evidence is
  reused within its original scope. Four unaltered actual captures are retained
  above; both laptop sizes/themes were inspected. The owned source server was
  stopped after verification.
- **102** affected local documentation links/anchors and evidence references
  passed, alongside accepted PR #8 source/layout preservation, E1–E42 preservation,
  source/review lock matching and read-only workflow structure. The dashboard is
  regenerated from the approved sequencing/progress records; freshness and Git
  whitespace checks are required with the final records.

Raw local runs, downloads, captured source hashes and diagnostics remain in the
original checkout's ignored `outputs/single-table-2026-10-15/`, with the final run
in `browser-final-reviewed/`. An initial static-file keyword error was fixed
before UI review. An early browser snapshot raced server draft acknowledgement;
the harness now awaits the draft state. Expanded help checks initially lacked a
touch-enabled browser context; that harness configuration was corrected. Earlier
passing runs are retained separately; the final run includes the completed Home
theme and explicit rule-editor checks. None of those failed attempts is counted
as final passing evidence.

The accepted PR #8 repair was published separately as
`cce10944339f6c857129fba9832d49d10e70a66d`. Both published source blobs match E42;
PR #8 merged at `d7d42f8bd183fd4bb3e7b9005ac7324b7a3d0b90`, and original local
main is synchronized. [Batch issue #9](https://github.com/Maks1m-Se/ravel/issues/9)
tracks the completed generator stages and joint code review. E46 records the
maintainer's current-app acceptance separately from automated verification.
The generator PR remains draft and unmerged. The maintainer grants a timing
exception for this publication batch only; normal Berlin restrictions remain
for subsequent work. Source implementation, checks, captures and documentation
were AI-assisted with Codex. Hosted core CI results remain pending execution;
no native installation, new server socket/DNS guard, physical disconnection,
native chooser/touch-device, screen-reader, other-platform UI, clinical or
binary-distribution validation is claimed.

## Workbook experiment

From the repository root on Windows with Python 3.11 installed:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r experiments/workbook/requirements.lock
.\.venv\Scripts\python.exe -m pip check
.\.venv\Scripts\python.exe -m experiments.workbook.app
```

Open **http://127.0.0.1:8080/** in a browser. Stop the server with Ctrl+C in its
terminal. No activation script is needed. Installation downloads dependencies;
subsequent operation uses local assets and loopback communication only. The
server binds to `127.0.0.1`, has no remote sharing enabled, and does not open a
browser automatically. Port 8080 must be free. This is a development launch,
not an installer or supported end-user distribution.

The lock was also recreated in a second local virtual environment using a
prepared wheel directory, then used for the final browser checks:

```powershell
.\.venv\Scripts\python.exe -m pip download --only-binary=:all: --dest outputs/nicegui-review/wheels -r experiments/workbook/requirements.lock
py -3.11 -m venv outputs/nicegui-review/fresh-env
.\outputs\nicegui-review\fresh-env\Scripts\python.exe -m pip install --no-index --find-links outputs/nicegui-review/wheels -r experiments/workbook/requirements.lock
.\outputs\nicegui-review\fresh-env\Scripts\python.exe -m pip check
```

The download step requires a connection. The `--no-index` installation uses
only those wheels. This verifies environment recreation on the same host; it is
not a clean-machine, installer or cross-platform test.

The [experiment](../experiments/workbook/app.py) uses one configuration model
for both entry paths. **Create from scratch** opens one numeric field with
defaults. **Start from a sample** loads the bundled
[invented ten-row CSV](../experiments/workbook/fixtures/sample.csv) and written
example suggestions (three fields, length range 9.8–12.2, zero missing values).
No inference runs, identifier fields are not fitted, and ten observations do
not establish population properties or associations.

Select a field, change its name/type, numeric bounds or missing percentage,
then **Apply**. Selecting another field applies valid edits first; invalid
edits remain visible for correction. Fields and Preview
share the same in-memory configuration and keep unfinished field edits. The
preview is fixed: it never regenerates or renames columns when settings change.
The scratch illustration contains three display values and is not source data.
The sample preview shows the original CSV. The experiment has one fixed table
per workbook and does not yet add fields or import arbitrary samples.

**Save configuration** validates the complete field/output candidate before
applying any field edits or downloading JSON. A failed Save preserves the applied
configuration, setting origins and all drafts; correct the error and retry.
**Reload configuration** opens a JSON chooser; loading replaces the current
workbook only after validation succeeds. Invalid files, including unsupported
oversized numeric values, leave applied settings and unfinished edits intact. The
format, `ravel-workbook-experiment/1`, is provisional, not the accepted application
recipe schema. Setting origins record defaults, sample suggestions and user
overrides relative to the original values. Save before leaving the page or
closing/restarting the server: there is no automatic persistence.

The compact workbench has a Light/Dark selector, a resizable Properties boundary
and Fields/Preview tabs. Badges beside each setting show the applied origin: **Default**, **Sample**
or **Edited**. A separate **Draft** marker and **Unapplied field edits** state
identify unfinished edits; badges do not relabel drafts as applied. The canonical
JSON origins remain `default`, `sample suggestion` and `user override`. Output
edits apply when valid; an invalid draft leaves the displayed applied counts
unchanged. The input label follows the mode: **New rows** or **Total rows**.

Question-mark help opens on hover or keyboard focus; click/tap pins it, and a
second click/tap or Escape closes it. Errors, session-only persistence, draft
state, counts-only status and **Fixed preview — not generated** stay visible.
Theme switching updates colors without rebuilding inputs. The selected theme
travels through Home and the two entry links; it is not part of saved JSON.

Manual interaction procedure retained for reproducibility. On 10 October the
maintainer reported all seven checks in their manual run passed on the earlier
compact-workbench build, including native save/reload and disconnected operation
(E24). This report applies to that tested build, not the subsequent alignment.
Required review of the aligned build is described under
[approved reference alignment](#approved-reference-alignment) and in
progress.json's next_action.

1. At browser **content** viewports 1366×657 and 1280×800, open **Create from
   scratch**. Use Tab/Shift+Tab and Enter to select **New table**, then **value**.
   Before pressing another key, expect focus in **Field name**. Run both themes
   and check readable labels, menus, dialogs, disabled bounds, unfocused input
   boundaries and visible focus.
   Open each help control by hover, focus and click/tap; dismiss with Escape.
2. Tab to **Minimum**, press Ctrl+A and enter `200`, then Tab to **Apply**
   and press Enter. Expect both bounds marked invalid, focus on Minimum and the
   whole range message beside it without scrolling manually. Correct to `5`
   and apply. Repeat with **Missing %** `150`, correcting to `15`.
   Before correcting, switch Light/Dark and back: drafts, errors and selected
   field must remain. Expect errors and Draft markers to clear after Apply,
   with the changed origin now Edited. Check unchanged settings retain their
   original badges.
3. Edit Maximum without applying, switch to **Preview** and back,
   and check the draft survives while the three illustrated values stay fixed.
   Switch themes while Preview is active; expect the same view and draft.
   Tab to the preview region and use arrow keys. Save JSON, edit again, then
   reload the saved file using the native chooser's keyboard controls. Expect
   saved settings and origins to return.
4. Return home and open **Start from a sample**. Expect three fields and ten
   invented rows, with marked sample suggestions. In `length_mm`, enter Missing
   % `150`, then activate **material**. Expect the selection to remain
   `length_mm`, an explanation in its panel, and focus on the invalid input.
   Correct to `15`, select material successfully, then return to length_mm.
5. With **New rows** and `1000`, expect **1,000 generated + 0 retained
   = 1,000 output**. Choose **Extend to total** using Enter/arrow keys:
   expect **10 retained + 990 generated = 1,000 total**. Draft Maximum `20`
   without applying, enter total `9`, then **Save configuration**. Expect focus
   and a full inline count error, no download, Maximum still `20` in the editor
   but its applied origin still **Sample**. Correct total to `1000`
   and Save; expect Maximum's origin to become **Edited**. Draft a new
   name and maximum, then reload the oversized fixture produced by the browser
   check below (`1366x657-sample-dark-oversized.json`). Expect a readable error;
   Cancel must leave both drafts intact. Reload the valid saved JSON and verify
   the complete configuration returns.
6. After installation, disconnect external networking using your normal
   controls, restart the server and repeat both paths in a fresh browser tab.
   Expect the same behavior without externally loaded assets. Review the
   proposed direction and report any confusing labels, keyboard traps or layout
   issues; this is UI acceptance, not clinical validation or framework adoption.

Initial experiment environment and observed checks on 9 October 2026 (E19;
the repair evidence below qualifies its validation/focus coverage):

| Item | Recorded evidence and scope |
| --- | --- |
| Python / dependencies | CPython 3.11.0 x64; NiceGUI 3.18.0; all 48 runtime packages pinned in [requirements.lock](../experiments/workbook/requirements.lock); pip 22.3 used for installation; `pip check` passed. This selects the experiment minor version only. |
| OS / browser | Windows 11 Home 26H2, build 26300.9550 x64; Chrome 154.0.8037.98, headless; Playwright 1.58.0 was isolated review tooling, not an application dependency. |
| State / counts | Six focused standard-library tests cover both configurations, canonical save/reload, provenance, atomic invalid edits, count boundaries and fixture expectations. Browser downloads/reloads also preserve canonical JSON across entry paths. |
| Keyboard / recovery | Tab, Enter and arrow-key controls exercised both entry paths, table/field selection, invalid range and count correction, switching views, and preview focus. Upload used browser automation, so native chooser interaction remains unverified. |
| Offline scope | Fresh Chrome context blocked non-loopback HTTP/WebSocket destinations; the server ran under a process-local socket/DNS guard rejecting non-loopback destinations. No external attempts or browser errors were observed. This was not an OS firewall, disconnected-machine or clean-machine release test. |
| Layout | Screenshots inspected at 1366×900; checks at 1366×768 and 1280×800 found no horizontal overflow, reachable labelled controls and visible input/preview focus. Vertical scrolling is expected. Native interactive review, other browsers, screen readers, Linux and macOS were not tested. |

The native computer/browser tools could not initialize (sandbox ACL/kernel
failure); headless Chrome was used instead. An initial browser assertion expected
`5` after reload but the equivalent display was `5.0`; the corrected numeric
assertion passed. Screenshot review prompted darker text on the pale action
button and persistent preview headers. No clinical or generated-data test is
claimed by these checks.

[Scratch path screenshot](images/m0-06-scratch.png) ·
[Sample path screenshot](images/m0-06-sample.png) ·
[Sample preview and count intent](images/m0-06-preview.png)

### Validation and keyboard repair checks

The bounded follow-up adds inline errors with `aria-invalid` and associated
messages, focus/scroll to the first invalid control, and atomic Save validation.
The provisional JSON format is unchanged. Focus after field selection awaits
NiceGUI's refresh and Vue's render flush through the stable page client; the old
unawaited refresh targeted a removed input. Quasar's layered `no-outline` rule
suppressed the original button outline, so buttons now use an inset focus ring.
Error messages occupy normal flow instead of Quasar's translated bottom area.
No application delay or new shortcut was added.

Maintained browser checks are in
[check_workbook_browser.py](../scripts/check_workbook_browser.py), with the
[offline server guard](../scripts/workbook_offline_server.py). Keep the ordinary
server stopped while running the guard. From the repository root, in terminal 1:

```powershell
.\.venv\Scripts\python.exe scripts/workbook_offline_server.py
```

After it reports the local server address, use terminal 2:

```powershell
py -3.11 -m venv outputs/workbook-review-env
.\outputs\workbook-review-env\Scripts\python.exe -m pip install -r experiments/workbook/requirements-review.lock
.\outputs\workbook-review-env\Scripts\python.exe scripts/check_workbook_browser.py --output outputs/workbench-themes/review
```

The review lock pins Playwright 1.58.0, pyee 13.0.1, greenlet 3.5.6 and
typing_extensions 4.16.0 separately from the runtime lock. Installation needs
network access. The check uses installed Chrome (`--channel chrome`) and does
not download a browser. Stop terminal 1 with Ctrl+C after the check. Use a new
`--output` directory for a later run to retain earlier evidence.

Repair verification on CPython 3.11.0 x64, Windows 11 Home 26H2 build
26300.9550, Chrome 154.0.8037.98 headless:

- **18 unit tests**: nine tracking and nine workbook tests, including combined
  valid-field/invalid-output Save, a 401-digit integer import and keyed errors.
- **Four browser cases**: both entry paths at 1366×657 and 1280×800. Assertions
  check immediate field focus before any navigation helper, computed focus
  styles and viewport screenshots, both invalid bounds, missing-percentage and
  count recovery, associated errors fully inside the viewport without control
  overlap, refused field selection, unchanged applied provenance/drafts and no
  download after failed Save, successful retry, oversized-import recovery,
  fixed previews, keyboard preview access, canonical save/reload and counts.
- Browser HTTP/WebSocket and server socket/DNS guards observed no external
  attempts and no browser page errors. Server stderr retained one Windows
  asyncio connection-teardown `ConnectionResetError` (WinError 10054); all four
  cases completed successfully. This diagnostic is retained, not suppressed.
  This remains process-local offline evidence, not a physically disconnected
  or clean-machine check.

Raw JSON results, downloaded invented configurations and screenshots are kept
locally in ignored `outputs/workbook-repair/final/`; the server guard writes
`outputs/workbook-repair/server-network.json`. Earlier failed runs remain under
`outputs/workbook-repair/run-*/`. They exposed the removed-input callback
context, absent ARIA association, Quasar error-slot precedence and overlapping
error layout. Harness failures also included startup readiness, a download
callback, an ambiguous alert locator and uploading before the dialog finished
closing/reopening; these were corrected with assertions/lifecycle waits. No
arbitrary application sleep was introduced. E19's earlier checks did not prove
combined Save atomicity or immediate field/button focus; E20 records this repair
without replacing that historical evidence.

Screenshots were inspected for both routes and viewport sizes. Native interactive
browser/chooser review, screen readers, other browsers/platforms and physical
network disconnection were not run. The automation supplies the file input
directly. Required maintainer review remains above and in progress.json.

Recommendation: **continue evaluating NiceGUI**, subject to maintainer UI review.
The shared editor and local assets work in the tested Windows/Chrome scope.
This repair resolves concrete focus/rendering and error-layout obstacles in the
candidate; application accessibility still needs deliberate integration/review.
Packaging still needs to carry a Python runtime/dependencies and provide a clear
local-server/browser launch and shutdown path. Native file-dialog behavior,
installer/signing choices, exact supported OS targets (including Apple silicon),
the release environment, benchmark hardware/frozen workload and clean-checkout /
clean-machine smoke evidence remain M0-06 work. No production profiling, random
generation, clinical derivation, installer or plugin loader was added. M0-06 is
partial; M0-07 and all ten release gates retain their pending/unverified scope.

### Public prototype review snapshot

On 9 October 2026, the maintainer reported successful range recovery and approved
the compact light/dark design direction. Only that interaction check is reported
as successful; full experiment acceptance and NiceGUI adoption remain pending.
The initial public snapshot `7f953af` retains the existing dark interface and
logo. Proposed themes were not implemented in that snapshot. Remaining interaction review and PR source review are the
next action in progress.json.

The README quickstart uses the pinned runtime lock and the existing
`python -m experiments.workbook.app` entry point. The public-review rerun passed
all 18 unit tests, dashboard freshness and whitespace checks, plus all four
maintained browser cases (both paths at 1366×657 and 1280×800) in the environment
recorded above. `pip check` passed. Browser blocking observed no external
HTTP/WebSocket requests or page errors. This rerun used the maintainer's already
running server; server stderr and the process-local socket/DNS guard were not
recaptured. Earlier guarded-run evidence and the Windows teardown diagnostic
remain in E19/E20; no new disconnected-machine claim is made.

Two unaltered application captures at 1366×960 were inspected:
[prototype sample workbook](images/m0-06-prototype-sample.png) and
[prototype inline validation recovery](images/m0-06-prototype-validation.png).
The second shows Minimum `200` rejected against Maximum `12.2`; correction to
`5` was then verified. These are screenshots of the running fixture prototype,
not mockups or generated datasets. Screenshot paths and README launch commands
were checked. Raw rerun results and capture evidence stay in ignored
`outputs/workbook-public-review/`, outside the commit. Native chooser, remaining
human interaction, screen-reader and cross-platform review remain outstanding.

### Compact workbench and theme checks

The approved follow-up keeps the existing R mark and replaces the workbook
header/tagline and large cards with a compact toolbar, narrow navigator, central
Fields/Preview area, Properties pane and count strip. Explicit Light/Dark colors
cover controls, labels, menus, dialogs, errors, disabled bounds and focus.
Secondary explanations use hover/focus/click/tap help. Applied Default/Sample/
Edited badges remain separate from unfinished Draft markers. The configuration
model, fixtures and provisional JSON format are unchanged.

Theme changes are presentation-only and preserve input elements, unfinished
values, associated errors, selected field, active view and applied configuration.
A focus trace exposed a queued Quasar selector-focus callback stealing focus
from a newly selected field after the menu transition. Before explicit field or
error focus, the app now calls the selectors' supported `blur` method to cancel
that pending focus, then awaits Vue's render flush. No arbitrary delay was added.
The browser helper also awaits menu opening and removal before continuing.

Current verification uses the maintained browser script across **eight cases**:
both routes, both themes, at 1366×657 and 1280×800 browser content viewports.
It retains the repair assertions described above and adds theme round trips with
invalid range/count drafts, refused-switch recovery, selected text fields with
disabled bounds, an active fixed Preview and saved/reloaded configuration.
Assertions check hover, focus, click/tap pinning and Escape dismissal of help,
rendered text contrast and visible keyboard-focus contrast. This is focused
coverage, not a general accessibility audit.

Final local results on 10 October 2026:

- **All eight maintained browser cases passed**. Theme cycles preserve canonical
  saved JSON as well as drafts, errors, field selection and the active view.
- **All 18 unit tests passed**; dashboard regeneration/freshness and Git
  whitespace checks passed. All 56 local Markdown file links resolve. README
  quickstart and all four clinical reference cases remain unchanged.
- Representative rendered text readings were at least **4.98:1**; checked focus
  rings were at least **6.11:1** against their rendered surfaces. Menu/dialog
  captures await transition completion. Screenshots were visually inspected for
  layout, error placement, focus and readable values at both viewport sizes.
- No external browser HTTP/WebSocket attempts or page errors were recorded.
  Final isolated-server stderr was empty; earlier Windows asyncio teardown
  diagnostics and failed runs remain retained. This does not broaden the
  offline/platform scope below.
- Final raw evidence is `outputs/workbench-themes/final-6/results.json`, with
  downloaded configurations and screenshots alongside it; the final server logs,
  preservation results and focus diagnosis are retained in the parent directory.

The tested environment remains CPython 3.11.0 x64, NiceGUI 3.18.0, Playwright
1.58.0 and Chrome 154.0.8037.98 headless on Windows 11 Home 26H2 build
26300.9550. Runtime and review locks remain unchanged. The commands above are
the reproducible setup/check commands; README has the ordinary launch command.
This run uses an isolated local review server at port 8081 and browser blocking
of non-loopback HTTP/WebSocket destinations. The process-local server socket/DNS
guard was not rerun for this follow-up; E19/E20 retain that earlier evidence.
Physical disconnection, native interactive browser/file-chooser review, screen
readers, other browsers/platforms and clean-machine installation remain unrun.

The E22 Light/Dark captures showed the running sample route at 1366×657: Light
with a maximum draft and its applied Sample origin; Dark with fixed rows,
retained invalid drafts and inline errors/focus. The public screenshot paths now
show the later alignment documented below; earlier captures remain in ignored
review outputs. Representative route, menu and dialog screenshots
from the maintained checks are also inspected locally; help visibility and
viewport placement are asserted by the browser checks. Raw JSON, focus traces,
downloaded invented configurations, screenshots and server logs stay in ignored
`outputs/workbench-themes/`. Earlier failures are retained, including focus
races and review-server startup readiness; they are not replacement pass evidence.

M0-06 remains partial and NiceGUI provisional. The maintainer's earlier successful
range check and approval of the direction do not accept this implementation or
the entire experiment. Required interaction and draft PR #4 source review remain
in progress.json's next_action. Continue evaluating NiceGUI subject to that
review: component focus/layered styling require deliberate integration, and
Python/server/browser packaging and launch/shutdown remain unresolved.

### Unfocused control-boundary repair

The scoped follow-up separates `--control-border` from `--line`. Enabled input
and selector outlines use `#72808d` in Light and `#7e8b97` in Dark; pane dividers,
table rules, badges and other existing separator colors still use the unchanged
line tokens. No layout, application logic, configuration or editing behavior
changed.

The maintained browser check measures the actual `::before` outline on all
visible, enabled, non-error, unfocused outlined inputs/selectors. It waits for
blur and CSS transitions to finish, verifies four solid visible edges, and
composites computed border color/opacity against both the control fill and its
surrounding surface. Every edge must reach **3:1 on both sides**. Disabled
controls and error/focus treatments retain their separate checks/scope. The
existing eight-case state, validation and immediate-focus assertions are retained.
Measurements run initially, after selecting a text field with disabled bounds
on the sample route, and after saving/returning through both themes.

A separate browser negative control temporarily applied the old divider colors:
the assertion correctly rejected **2.13:1 Light** and **1.89:1 Dark** against the
surrounding surface. The initial injected-style probe ran during the border
transition; waiting for actual transition completion made this probe reliable.
This was a check-lifecycle adjustment, not an application delay or editing change.

For E23, the actual Light/Dark screenshots were refreshed and inspected.
The Light capture keeps the unapplied maximum edit while focus is on Save, making
all input boundaries unfocused; the Dark capture retains fixed preview rows,
invalid range drafts and immediate error focus. Previous captures and the
pre-repair snapshot are retained under ignored `outputs/workbook-border-contrast/`;
the earlier review ZIP also remains unchanged. E22's text/focus checks are
historical evidence and did not establish unfocused-boundary contrast.

Final scoped results on 10 October 2026: **all eight maintained browser cases
passed**, including all earlier state, validation, focus, fixed-preview,
count and canonical round-trip assertions. Unfocused enabled-control outlines
measured at least **4.05:1 Light** and **4.38:1 Dark** against both adjacent
surfaces. No external browser HTTP/WebSocket attempts or page errors were
recorded. The server log retains a Windows asyncio connection-teardown
`ConnectionResetError` (WinError 10054); it is not suppressed or treated as a
clean stderr result. Final browser results, downloaded invented configurations,
viewport captures, negative-control measurements and server logs are retained
in ignored `outputs/workbook-border-contrast/`. All 18 unit tests, dashboard
regeneration/freshness, local screenshot links and Git whitespace checks passed.

For reproduction, use the same locked setup and review commands above with a new
output directory. The local rerun uses the isolated port-8081 launcher and:

```powershell
.\outputs\workbook-review-env\Scripts\python.exe scripts/check_workbook_browser.py --base-url http://127.0.0.1:8081 --output outputs/workbook-border-contrast/final
```

The Python/NiceGUI/Playwright/Windows/Chrome environment is unchanged. Browser
non-loopback HTTP/WebSocket blocking remains scoped browser evidence; server
socket/DNS guards, physical disconnection, native chooser/human acceptance,
screen readers, other platforms and clean-machine checks are not rerun here.
M0-06 remains partial, NiceGUI provisional and PR #4 draft; all release gates and
open maintainer review items remain unchanged.

### Approved reference alignment

The 10 October maintainer report records **all seven manual checks passed** on
the pre-alignment compact-workbench build (E22/E23), including native save/reload
and physically disconnected operation. This is attributed maintainer evidence,
not an automated observation or clean-machine/cross-platform claim. Earlier
pending-check statements above describe their historical snapshots. Visual
alignment and acceptance of this subsequent pass remain pending.

The supplied `ravel-approved-workbench-reference.html` is a visual reference
only. Its illustrative field names, values and demo logic are not application
requirements. The app retains `item_id`, `material`, `length_mm`, the 9.8–12.2
sample range and 0% missing, its configuration model, validation, atomic Save,
provenance and draft behavior. No dependencies or clinical rules changed.

This bounded pass restores neutral grey/graphite panes and blue accents while
keeping the existing green R mark. Three small original SVG toolbar icons are
served from the app's local static route; there is no icon CDN. Properties uses
paired bounds with full inline errors, applied origin badges and separate Draft
markers. The Settings column reads applied configuration only, including full
numeric values and missing percentages. Text fields say Text without inventing
category or identifier rules. Hover/focus/click/tap/Escape help is centered beside
its label. Assumptions expands with click or Enter/Space. The count strip spans
the panes and retains applied-count, invalid-draft and counts-only labels.

Required visual/source review for this aligned build:

1. Launch with the documented command above, open `/sample` and compare Fields
   in both themes against the approved HTML. Expect grey/graphite panes, blue
   selection/actions, the existing logo, three toolbar icons, compact Properties
   and one count strip. Edit Maximum to `20`: Settings must remain
   `9.8–12.2 · 0% missing` with Sample origin and a separate Draft indicator.
   Apply: expect `9.8–20 · 0% missing` and Edited origin.
2. Enter Minimum `200`, Apply, then view Preview. Expect both complete range
   errors, retained drafts and fixed source rows. Switch themes; state must stay.
   Correct Minimum to `5` and Apply. Open Assumptions by keyboard and mouse;
   expect the individual-field/relationship/fixed-preview limitations. Check
   adjacent help via hover, focus, click/tap and Escape.
3. Review draft PR #4 source and the actual captures below. Record accept/change
   feedback against progress.json's next_action. The earlier seven-check report
   does not approve these new visual changes or adopt NiceGUI.

Remaining visual differences from the reference are deliberate: Properties is
312 px rather than 235 px at tested laptop widths to accommodate applied origin,
draft state and complete per-input errors; Quasar retains floating labels and
selectors; the app shows a persistent status line and fuller count/session
labels. The fixed preview contains all ten actual fixture rows. These differences
are for maintainer review, not a claim of pixel equivalence.

[Light Fields](images/m0-06-workbench-light.png) ·
[Dark Fields](images/m0-06-workbench-dark.png) ·
[Light validation](images/m0-06-validation-light.png) ·
[Dark validation](images/m0-06-validation-dark.png)

Final verification on 10 October 2026:

- All **18 unit tests** and **eight maintained browser cases** passed (both entry
  paths and themes at 1366×657 and 1280×800). Existing validation, immediate focus,
  refused-switch, atomic failed Save/retry, oversized import, fixed preview,
  counts, theme preservation and canonical JSON round-trip assertions remain.
  Added checks cover local icon loading, centered adjacent help behavior,
  keyboard Assumptions, paired complete errors and Settings isolation from drafts
  and failed operations, followed by Apply/Save/reload updates.
- Minimum measured contrast (text / focus / enabled boundaries, against both
  adjacent surfaces): **Light 4.76:1 / 4.45:1 / 3.23:1**; **Dark 5.91:1 / 5.19:1 / 3.63:1**. Text must reach 4.5:1;
  focus and boundaries must reach 3:1. Boundary checks include inputs/selectors,
  Apply and help buttons. This is focused rendered-state coverage, not a complete
  accessibility audit.
- Four actual 1366×657 captures above were inspected against both locally
  rendered reference themes, including complete paired range errors. Correction
  to Minimum 5 passed. Expanded Assumptions and an unrounded `1.23456789` Settings
  summary were also checked. The Properties pane can scroll when explanations
  are expanded at the shorter viewport.
- Dashboard regeneration/freshness, **61 local Markdown links/anchors**, unchanged
  model/fixture/lock/clinical-contract checks, runtime and review `pip check`, and
  Git whitespace checks passed. Historical E1–E23 and all task/milestone/release
  gate statuses remain unchanged; E24 records the maintainer report separately.
- Final browser guards recorded **no external HTTP/WebSocket attempts or page
  errors**; the isolated port-8081 server stderr was empty. Environment remains
  CPython 3.11.0 / NiceGUI 3.18.0 / Playwright 1.58.0 / Chrome 154.0.8037.98
  headless on the Windows host recorded above. Native/disconnected operation was
  not rerun on this aligned build, nor were server socket/DNS guards, screen
  readers, other browsers/platforms or clean-machine checks.

The initial guarded port-8080 launch failed because an existing server occupied
the port. That server was preserved; the resulting old-server browser run is not
new-build evidence. A later new-build run found the Properties help popup clipped
at its pane edge; its placement was corrected before all eight cases passed.
Final runs are retained in ignored `outputs/workbench-alignment/final/`, with
logs, previous screenshots and rendered reference captures in the parent folder.
To repeat the maintained check, use the documented setup/launcher and:

```powershell
.\outputs\workbook-review-env\Scripts\python.exe scripts/check_workbook_browser.py --output outputs/workbench-alignment/review
```

For an already running isolated review server, pass its loopback URL with
`--base-url`; this pass used `http://127.0.0.1:8081`. M0-06 remains partial,
NiceGUI provisional and PR #4 draft, pending maintainer visual/source review.

### Fresh-checkout smoke

On 11 October 2026 the actual local starting commit was
`55f02e5b92fc20d044ac575cba8c6a48fd2bd14e`, on
`experiment/m0-06-nicegui-workbook`, with a clean working tree. A local isolated
clone and new virtual environment passed all **48 runtime pin checks**, `pip
check`, **18 unit tests**, dashboard freshness and **eight maintained browser
cases** (both entry paths/themes at 1366×657 and 1280×800). Browser checks include
local assets/icons, validation, drafts, count meanings and canonical save/reload;
no external HTTP/WebSocket attempts or page errors were observed. This is a
fresh checkout on the **same Windows host**, not a clean-machine test.

Recorded commands from `C:\Git\ravel` (use unused destination/output paths when
repeating; runtime wheel preparation is documented above):

```powershell
git -c safe.directory=C:/Git/ravel clone --no-hardlinks --branch experiment/m0-06-nicegui-workbook C:/Git/ravel outputs/m0-06-packaging-2026-10-11/checkout
.\.venv\Scripts\python.exe -m venv outputs/m0-06-packaging-2026-10-11/checkout/.venv
.\outputs\m0-06-packaging-2026-10-11\checkout\.venv\Scripts\python.exe -m pip install --no-index --find-links outputs/nicegui-review/wheels -r outputs/m0-06-packaging-2026-10-11/checkout/experiments/workbook/requirements.lock
Set-Location outputs/m0-06-packaging-2026-10-11/checkout
.\.venv\Scripts\python.exe -m pip check
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe scripts/build_dashboard.py --check
.\.venv\Scripts\python.exe -c "from nicegui import ui; import experiments.workbook.app; ui.run(host='127.0.0.1', port=8082, title='Ravel | Workbook experiment', dark=True, reload=False, show=False, prod_js=True, on_air=False)"
```

In a second terminal, from `C:\Git\ravel`, reuse the existing review environment:

```powershell
.\outputs\workbook-review-env\Scripts\python.exe outputs/m0-06-packaging-2026-10-11/checkout/scripts/check_workbook_browser.py --base-url http://127.0.0.1:8082 --output outputs/m0-06-packaging-2026-10-11/fresh-browser
```

The ordinary development server was preserved; the port-8082 test server was
stopped after checking. Raw environment evidence and results stay in ignored
`outputs/m0-06-packaging-2026-10-11/`. Native chooser, physical disconnection,
screen readers and other platforms were not retested. Existing screenshots apply.

### Windows folder-bundle experiment

The single approach uses the installed [NiceGUI 3.18.0 packaging wrapper](https://github.com/zauberzeug/nicegui/blob/v3.18.0/nicegui/scripts/pack.py)
with [PyInstaller one-folder mode](https://pyinstaller.org/en/v6.20.0/operating-mode.html#bundling-to-one-folder).
The [build recipe](../scripts/build_workbook_windows.py) verifies the runtime and
[separate build lock](../experiments/workbook/requirements-build.lock), includes
CSS/icons/fixture data and the runtime marks/favicons from canonical `brand/`,
and saves the command/log/spec under a new output directory.
It directs user-site and PyInstaller cache paths into that directory. The pinned
wrapper calls `pyinstaller` by name on Windows and does not propagate its exit
status; the recipe supplies the environment's Scripts path and checks artifacts.
The [console launcher](../experiments/workbook/bundle_entry.py) keeps the existing
app behavior, binds loopback, defaults to port 8083 and supports `--runtime-info`
for verifying frozen import paths. Runtime/review dependencies are unchanged.

Reusable build commands from the repository root (installation may use network):

```powershell
py -3.11 -m venv outputs/workbook-build-env
.\outputs\workbook-build-env\Scripts\python.exe -m pip install -r experiments/workbook/requirements.lock -r experiments/workbook/requirements-build.lock
.\outputs\workbook-build-env\Scripts\python.exe -m pip check
.\outputs\workbook-build-env\Scripts\python.exe scripts/build_workbook_windows.py --output outputs/workbook-windows
```

The recorded build instead reused the fresh checkout's newly created environment,
copied only the three new packaging files into it, installed PyInstaller 6.20.0
and verified the captured build pins. Its successful invocation was:

```powershell
.\outputs\m0-06-packaging-2026-10-11\checkout\.venv\Scripts\python.exe outputs/m0-06-packaging-2026-10-11/checkout/scripts/build_workbook_windows.py --output outputs/m0-06-packaging-2026-10-11/build-2
Copy-Item -LiteralPath outputs/m0-06-packaging-2026-10-11/build-2/dist/Ravel-workbook -Destination outputs/m0-06-packaging-2026-10-11/standalone/Ravel-workbook -Recurse
```

Wait for the whole folder copy to finish; distribute the **entire folder**, not
just the executable. First build failure: `PermissionError: [WinError 5]` probing
the roaming Python user-site directory. Isolating user-site/cache paths resolved
it within the same approach. The build retains an optional `tzdata` hidden-import
warning. A launch before copying finished failed on missing extension modules;
the completed copy passed, with no rebuild or dependency changes. Failed logs
are retained alongside `build-2/build.log`.

The copied bundle was tested while the original checkout/build environment was
temporarily renamed, with Python environment variables removed, Windows-only
PATH and a working directory outside the checkout. Frozen app, fixture and import
paths all resolved inside the bundle; five assets were byte-identical to source.
It contains **63,915,291 bytes (60.95 MiB), 1187 files**. One observed startup
to first HTTP 200 was **2.68 seconds**; this is not a startup benchmark.
All **eight maintained browser cases passed** at port 8083, including both routes,
themes, validation and canonical save/reload. No external browser HTTP/WebSocket
attempts or page errors occurred; final bundle stderr was empty. The review
environment was a separate test driver, not a dependency of the executable.

Reproducible launch of the already built result (the maintainer completed the
validation correction, native JSON save/reload and shutdown checks on 11 October):

```powershell
.\outputs\m0-06-packaging-2026-10-11\standalone\Ravel-workbook\Ravel-workbook.exe --port 8083
```

Open `http://127.0.0.1:8083/`, try both entry paths/themes, reject Minimum `200`,
correct it to `5`, then Save and Reload JSON. Expect complete inline errors,
preserved applied/draft state and saved settings/origins to return. Ctrl+C in
the console stops the server. An existing browser is required. This same-host
Windows experiment does not supply an installer/signature, clean-machine or
cross-platform evidence, or framework adoption. M0-06 remains partial, NiceGUI
provisional and visual/source acceptance pending. Build/test artifacts are ignored;
the useful recipe, launcher, build lock and evidence were prepared locally for review.
Published UI screenshots are reused. The original development server is preserved.

On 11 October the maintainer reported bundled validation correction, native JSON
save/reload, Ctrl+C shutdown and preservation of the original development server
all passed. This applies to the tested same-host folder bundle; it does not accept
visuals or establish clean-machine/cross-platform readiness. ChatGPT source review
of the packaging archive against `55f02e5` reproduced all six changed files and
passed nine tracking tests and dashboard freshness; the malformed Windows paths
found in that review are corrected here. These are reported review results, not
new independent application tests.
Final handoff checks passed: nine tracking tests, dashboard regeneration/freshness,
64 local links/anchors, Python compilation and Git whitespace. Historical evidence
and all task/milestone/release-gate statuses are preserved.

Preparation follow-up on 11 October: nine tracking tests, dashboard freshness,
85 local Markdown links/anchors and source-preservation checks passed. The
repaired setup blocks were extracted from this document and parsed as PowerShell;
directories, executable/script/lock paths and `--version`/bundle `--help` checks
passed. Only an isolated empty build environment was created for path checking;
installation, builds and application browser tests were not repeated. Host policy
blocked running the checker as a script file; its checks ran inline without
changing that policy. The notice collection was corrected after its first audit
found newline duplication and implementation files under a directory named
`licenses`; all 77 retained installed notice texts and five retrieved frontend
license texts now match their source texts after declared whitespace normalization.
The prior successful application checks apply because application code/assets and
locks are unchanged. Raw preparation evidence is ignored under
`outputs/m0-06-preparation-2026-10-11/`. This preparation was kept local and
uncommitted until the maintainer authorized publication on Sunday, 11 October.
The Berlin 08:00–16:30 publishing restriction applies Monday–Friday only.

On 11 October the maintainer authorized integrating PR #4 into main with a merge
commit, preserving all existing commits and without a release/tag/binary
publication. Main's README-only `e1be2d0` overlapped the reviewed `e2814bc`
README; integration retains the compact version and one Dark screenshot, and
changes the quickstart to a normal repository checkout. All 18 unit/tracking
tests and 80 local document/image/anchor checks passed; application code,
fixtures, assets and dependency locks are unchanged, so recorded browser evidence
is reused. Earlier draft-PR instructions describe the historical review stage.
Merge authorization does not accept visual alignment, adopt the proposed
platform/environment choices or satisfy any release gate.

### Isolated Python 3.14 compatibility trial

On 11 October 2026, branch `experiment/m0-06-python314` started from clean main
`a6abeb97d032f4b0143600b189ac22a6af7bea43`. The [official release page](https://www.python.org/downloads/release/python-3148/)
and [Windows downloads](https://www.python.org/downloads/windows/) confirmed
3.14.8 before installation. The x64 installer SHA-256 was
`759be887b96e736a3ca886daf8d575f18fcae1a09efab6902f42d59e8999f8ef`;
Authenticode was Valid with Python Software Foundation as signer. Installation
used an ignored trial directory without PATH, launcher binary, file association
or shortcut changes. The existing `.venv` and explicit `py -3.11` remain 3.11.0;
this does not replace the documented working setup.

These PowerShell commands run from `C:\Git\ravel`. The paths below identify the
recorded run; use a new trial root/output directory when repeating, so old results
and bundles are not overwritten. Keep the existing development server running;
this trial verified ports 8092/8093 were unused before starting.

```powershell
$trialRoot = Join-Path (Get-Location) 'outputs/python314-trial-2026-10-11'
New-Item -ItemType Directory -Path $trialRoot
$installer = Join-Path $trialRoot 'python-3.14.8-amd64.exe'
Invoke-WebRequest https://www.python.org/ftp/python/3.14.8/python-3.14.8-amd64.exe -OutFile $installer
if ((Get-FileHash -LiteralPath $installer -Algorithm SHA256).Hash.ToLower() -ne '759be887b96e736a3ca886daf8d575f18fcae1a09efab6902f42d59e8999f8ef') { throw 'Installer hash mismatch' }
if ((Get-AuthenticodeSignature -LiteralPath $installer).Status -ne 'Valid') { throw 'Installer signature invalid' }
$installerArgs = @('/quiet', 'InstallAllUsers=0', ('TargetDir=' + $trialRoot + '\python'), 'Include_launcher=0', 'InstallLauncherAllUsers=0', 'PrependPath=0', 'AssociateFiles=0', 'Shortcuts=0', 'Include_test=0', 'Include_doc=0', 'Include_tcltk=0', 'Include_pip=1', 'Include_freethreaded=0', '/log', ($trialRoot + '\install.log'))
$installProcess = Start-Process -FilePath $installer -ArgumentList $installerArgs -WindowStyle Hidden -Wait -PassThru
if ($installProcess.ExitCode -notin @(0, 3010)) { throw ('Installer exit ' + $installProcess.ExitCode) }
.\outputs\python314-trial-2026-10-11\python\python.exe -c "import sys,sysconfig,struct; print(sys.version); assert sys.version_info[:3] == (3,14,8); assert struct.calcsize('P')*8 == 64; assert sys._is_gil_enabled(); assert not sysconfig.get_config_var('Py_GIL_DISABLED')"
.\outputs\python314-trial-2026-10-11\python\python.exe -m venv outputs/python314-trial-2026-10-11/runtime-env
.\outputs\python314-trial-2026-10-11\python\python.exe -m venv outputs/python314-trial-2026-10-11/build-env
.\outputs\python314-trial-2026-10-11\python\python.exe -m venv outputs/python314-trial-2026-10-11/review-env
```

The recorded install used `--no-index --find-links
outputs/m0-06-preparation-2026-10-11/cp314-wheel-probe`, reusing prepared wheels.
To prepare those exact pins on a repeat (network needed), download with the new
interpreter before the following installs:

```powershell
.\outputs\python314-trial-2026-10-11\python\python.exe -m pip download --only-binary=:all: --dest outputs/python314-trial-2026-10-11/wheels -r experiments/workbook/requirements.lock -r experiments/workbook/requirements-build.lock -r experiments/workbook/requirements-review.lock
.\outputs\python314-trial-2026-10-11\runtime-env\Scripts\python.exe -m pip install --no-index --find-links outputs/python314-trial-2026-10-11/wheels -r experiments/workbook/requirements.lock
.\outputs\python314-trial-2026-10-11\build-env\Scripts\python.exe -m pip install --no-index --find-links outputs/python314-trial-2026-10-11/wheels -r experiments/workbook/requirements.lock -r experiments/workbook/requirements-build.lock
.\outputs\python314-trial-2026-10-11\review-env\Scripts\python.exe -m pip install --no-index --find-links outputs/python314-trial-2026-10-11/wheels -r experiments/workbook/requirements-review.lock
.\outputs\python314-trial-2026-10-11\runtime-env\Scripts\python.exe -m pip check
.\outputs\python314-trial-2026-10-11\build-env\Scripts\python.exe -m pip check
.\outputs\python314-trial-2026-10-11\review-env\Scripts\python.exe -m pip check
.\outputs\python314-trial-2026-10-11\runtime-env\Scripts\python.exe -m unittest discover -s tests -v
.\outputs\python314-trial-2026-10-11\runtime-env\Scripts\python.exe scripts/build_dashboard.py --check
.\outputs\python314-trial-2026-10-11\runtime-env\Scripts\python.exe -m experiments.workbook.bundle_entry --port 8092 --runtime-info
```

In another terminal at the same root, check the runtime server:

```powershell
.\outputs\python314-trial-2026-10-11\review-env\Scripts\python.exe scripts/check_workbook_browser.py --base-url http://127.0.0.1:8092 --output outputs/python314-trial-2026-10-11/runtime-browser
```

Stop only that trial server after its checks (Ctrl+C in its terminal), then use
one unchanged packaging approach:

```powershell
.\outputs\python314-trial-2026-10-11\build-env\Scripts\python.exe scripts/build_workbook_windows.py --output outputs/python314-trial-2026-10-11/build-original
New-Item -ItemType Directory -Path outputs/python314-trial-2026-10-11/standalone
Copy-Item -LiteralPath outputs/python314-trial-2026-10-11/build-original/dist/Ravel-workbook -Destination outputs/python314-trial-2026-10-11/standalone/Ravel-workbook -Recurse
Set-Location outputs/python314-trial-2026-10-11/standalone/Ravel-workbook
$env:PYTHONPATH = $null
$env:PYTHONHOME = $null
$env:VIRTUAL_ENV = $null
$env:PATH = "$env:SystemRoot\System32;$env:SystemRoot"
.\Ravel-workbook.exe --port 8093 --runtime-info
```

Run the browser check in a separate terminal with normal environment variables,
from `C:\Git\ravel`; the test driver is not an executable dependency:

```powershell
.\outputs\python314-trial-2026-10-11\review-env\Scripts\python.exe scripts/check_workbook_browser.py --base-url http://127.0.0.1:8093 --output outputs/python314-trial-2026-10-11/bundle-browser
```

`--runtime-info` must show `frozen: true` and executable/app/fixture/import paths
inside the copied folder. The trial also byte-compared the bundled
`_internal/python314.dll` to the verified official installation's DLL and CSS,
three SVG icons and CSV to source. Stop only this trial bundle after checking.
Distribute the entire folder for any later review, not just its executable.

Observed environment: standard GIL-enabled CPython **3.14.8**,
`MSC v.1944 64 bit (AMD64)`; Windows 11 Home **26H2 build 26300.9550**; NiceGUI 3.18.0,
PyInstaller 6.20.0/hooks 2026.8, Playwright 1.58.0 and installed headless
**Chrome 154.0.8037.98**.
All 48 runtime, seven build and four review pin/version checks and all three
`pip check` runs passed. All **18 unit/tracking tests** and **eight runtime
browser cases** passed; the original recipe built successfully in about 52 seconds.
The complete copy contains **69,778,736 bytes (66.55 MiB), 1190 files**; one
observed startup to HTTP 200 was **2.62 seconds**, not a benchmark.
All **eight standalone-bundle browser cases passed** as well, covering both
routes/themes at 1366×657 and 1280×800, local assets, validation/recovery,
provenance/drafts, fixed previews/counts and canonical save/reload. Both runs
recorded zero external HTTP/WebSocket attempts and page errors; both server stderr
logs were empty. Trial servers on 8092/8093 were stopped by verified process
identity, including their children only. Original port-8080 server PID 15316 was
preserved and still returned HTTP 200. No native chooser/disconnection check was
performed in this trial.

The separate diagnostic command below failed on pinned setuptools 65.5.0 with `pkgutil.ImpImporter` absent. This is a
real tooling limitation despite successful metadata checks; PyInstaller logged the same failure as a nonfatal
`SetuptoolsInfo` warning and continued. The artifact passes do not establish
setuptools API compatibility. A candidate setuptools 80.9.0 wheel was prepared
but not installed. **No pin, candidate lock, recipe or application repair was
needed for the tested pipeline.** Keep the unsupported import explicit when
reviewing a future build environment. The existing review script emits a
SyntaxWarning for a JavaScript `\d` escape; this does not fail its cases. Build
logs retain the setuptools probe warning and optional hidden-import `tzdata` warning.

```powershell
.\outputs\python314-trial-2026-10-11\build-env\Scripts\python.exe -c "import setuptools"
```

Raw installer/install/build logs, environment/version data, browser results,
DLL/path/asset verification, diagnostic failure, captures and binaries remain in
ignored `outputs/python314-trial-2026-10-11/`. This is a **same-host** Windows
trial, not a clean-machine, other-platform, physical-offline, native-chooser or
redistribution approval. Appearance is unchanged; published screenshots are
reused. Python 3.11 setup, original locks and historical evidence are preserved;
M0-06 remains partial, NiceGUI provisional, proposals unadopted and gates unverified.
Final documentation checks passed: 81 local links/images/anchors, extracted
PowerShell command syntax, dashboard regeneration/freshness and Git whitespace.

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
commands verify project tracking and the workbook configuration/count contracts;
they do not establish generation or clinical validation or release readiness.

### Python 3.14 candidate build lock

Follow-up to E32 on `experiment/m0-06-python314`, starting at `e0bb48a`.
PyInstaller 6.20.0's installed `METADATA` explicitly requires
`setuptools>=42.0.0`; its `utils/hooks/setuptools.py` imports setuptools in an
isolated probe. It is **not removable as an unused pin**. The original
65.5.0 `pkgutil.ImpImporter` failure and successful fallback build remain E32
evidence. The separate [candidate lock](../experiments/workbook/requirements-build-python314-candidate.lock)
changes only `setuptools==65.5.0` to `setuptools==80.9.0`. The prepared wheel is
tested here, not accepted as the supported version or a security-reviewed choice.
Its installed metadata requires Python >=3.9; no latest-version upgrade was attempted.
See the [dependency inventory](dependency-licenses.md#python-314-candidate-build-dependency)
for inspected source files and retained notices.

Reproduction from `C:\Git\ravel` (choose a new output folder and unused port on
repeat; previous logs/environments/binaries must not be overwritten):

```powershell
Set-Location C:\Git\ravel
$candidateRoot = Join-Path (Get-Location) 'outputs\python314-setuptools-candidate-2026-10-11'
$python314 = Join-Path (Get-Location) 'outputs\python314-trial-2026-10-11\python\python.exe'
& $python314 -m venv "$candidateRoot\build-env"
$candidatePython = "$candidateRoot\build-env\Scripts\python.exe"
& $candidatePython -m pip install --no-index --find-links .\outputs\m0-06-preparation-2026-10-11\cp314-wheel-probe --find-links .\outputs\python314-trial-2026-10-11\candidate-wheels -r experiments/workbook/requirements.lock -r experiments/workbook/requirements-build-python314-candidate.lock
& $candidatePython -m pip check
& $candidatePython -c "from importlib.metadata import version; from pathlib import Path; locks=[Path('experiments/workbook/requirements.lock'),Path('experiments/workbook/requirements-build-python314-candidate.lock')]; pins=[line.split('==') for lock in locks for line in lock.read_text().splitlines() if '==' in line and not line.startswith('#')]; assert all(version(name)==expected for name,expected in pins); print(len(pins),'exact pins')"
& $candidatePython -c "import setuptools, altgraph, packaging, pefile, PyInstaller, _pyinstaller_hooks_contrib, win32ctypes, nicegui.scripts.pack; from PyInstaller.utils.hooks.setuptools import setuptools_info; assert setuptools_info.available and setuptools_info.version == (80,9,0); print('build imports and probe passed')"
& $candidatePython scripts/build_workbook_windows.py --build-lock experiments/workbook/requirements-build-python314-candidate.lock --output "$candidateRoot\build"
New-Item -ItemType Directory -Path "$candidateRoot\standalone" -ErrorAction Stop
Copy-Item -LiteralPath "$candidateRoot\build\dist\Ravel-workbook" -Destination "$candidateRoot\standalone\Ravel-workbook" -Recurse
```

For new prepared wheels, download the unchanged runtime lock plus candidate build
lock using the isolated interpreter's `pip download --only-binary=:all: -r ...`;
the actual run used the two existing wheel folders shown above. The recipe's
default remains `requirements-build.lock`; explicit `--build-lock` is required.
Three focused tests verify original default acceptance, candidate rejection under
the default and explicit candidate acceptance. Runtime/application code and pins
are unchanged: E32's eight runtime browser cases are reused.

Start the copied bundle from its own folder with Python environment variables
removed and Windows-only PATH as in the preceding trial; use port **8094** and
`--runtime-info`. Frozen executable/app/fixture and all import paths (now also
`_internal/setuptools/_vendor`) must stay inside that copied folder. Check the
five CSS/SVG/CSV assets and `python314.dll` against the unchanged source and
official 3.14.8 installation, as in E32.

In a dedicated terminal (discard its environment changes when finished):

```powershell
Set-Location C:\Git\ravel\outputs\python314-setuptools-candidate-2026-10-11\standalone\Ravel-workbook
$env:PYTHONPATH = $null
$env:PYTHONHOME = $null
$env:VIRTUAL_ENV = $null
$env:PATH = "$env:SystemRoot\System32;$env:SystemRoot"
.\Ravel-workbook.exe --port 8094 --runtime-info
```

Run the check from a second terminal with normal environment variables:

```powershell
.\outputs\python314-trial-2026-10-11\review-env\Scripts\python.exe scripts/check_workbook_browser.py --base-url http://127.0.0.1:8094 --output outputs/python314-setuptools-candidate-2026-10-11/bundle-browser
```

Use Ctrl+C in the dedicated bundle terminal when finished. The automated trial
instead verified the recorded executable path before stopping its process tree.

Actual raw evidence is in ignored `outputs/python314-setuptools-candidate-2026-10-11`:
`candidate-inspection.json`/`imports.log`, `build/build.log`, `bundle-launch.json`,
`verify_bundle_launch.py`, `bundle-browser/results.json` and cleanup/check logs.
All **55 exact pins**, `pip check`, eight build-tool imports and the isolated
setuptools probe passed. The build finished in about **56 seconds** without
`ImpImporter` or `SetuptoolsInfo: failed to obtain` errors; the optional `tzdata`
warning remains. Complete copied bundle: **71,204,215 bytes (67.91 MiB), 1,198
files**, one **2.67-second** HTTP startup observation. Frozen paths/DLL/assets
passed. Bundle browser and final documentation results are recorded in E33.
All eight cases passed; browser external HTTP/WebSocket attempts and page errors
were empty, as was bundle stderr. The existing browser script's invalid-escape
SyntaxWarning remains (PowerShell records it as a native error even though the
browser results pass); no application/test-driver behavior repair was needed.
Only this trial's verified bundle process tree is stopped; preserve port 8080
and Python 3.11. No appearance change; published screenshots remain current.

Recommendation: review this tested candidate replacement rather than remove a
declared dependency. Keep original locks/defaults and Python 3.11 until maintainer
adoption. This does not establish clean-machine, other-platform, physical-offline,
native-dialog, benchmark, security or redistribution approval. New setuptools
vendor inclusion still needs artifact/source-obligation mapping. M0-06 partial,
NiceGUI provisional, proposals unadopted and release gates unchanged.

### Private clean-Windows review preparation

PR [#5](https://github.com/Maks1m-Se/ravel/pull/5) merged the reviewed
`22428f4a0b696a567bda8196f07006459a92d14e` by merge commit
`edec6d62e14e9a2e36cfdf06c9635190c68e95a8` on 11 October 2026. Main already
was an ancestor: no integration changes, and local main matched the reviewed tree
exactly. E32/E33 checks remain valid and are reused. This accepts the experiment
record/candidate tooling for integration, **not Python 3.14 adoption**; original
Python 3.11 defaults/locks, partial M0-06 and release gates remain intact.

Read-only local inspection found no accessible `Get-VM`, `VBoxManage` or `vmrun`.
An unidentified `vmwp.exe` process existed, but its command line was unavailable
and `root/virtualization/v2` was an invalid namespace. No authorized clean Windows
guest or separate machine could be established. Its OS and Python absence were
**not verified**. No Windows feature or virtualization platform was enabled or
installed, and no clean-machine execution has happened.

The private archive, kept ignored and not uploaded or published, is:

```text
C:\Git\ravel\outputs\private-windows-review-2026-10-11\ravel-python314-setuptools8090-windows-x64-review.zip
SHA-256: 2b13d1faa22714f8fb9a5f41df0c963baa342d5b4a74377025020658c262cd2e
Size: 35,192,969 bytes (33.56 MiB)
```

It includes the **complete E33 tested standalone folder**: standard GIL-enabled
CPython 3.14.8 x64 / NiceGUI 3.18.0 / candidate setuptools 80.9.0, all **1,198
bundle files (71,204,215 bytes)**. Four accompanying files are `REVIEW.md`,
`THIRD-PARTY-NOTICES.txt` (the current collection), Ravel `LICENSE` and a per-file
`bundle-manifest.json`; the ZIP has **1,202 files**. Private packaging does not
complete redistribution review: frontend/native/vendor mapping, source obligations
and artifact notice completeness remain open.

Actual archive verification: ZIP CRC passed, full extraction completed, and every
extracted file's size/SHA-256 matched staging. All bundle files matched the E33
tested standalone and original build folders. Raw guide/staging/extraction,
manifest and `archive-verification.json` remain under ignored
`outputs/private-windows-review-2026-10-11`. This is **archive verification on
the development host**, not a clean-machine launch or another browser run.

Required maintainer check on an authorized genuinely clean Windows x64 machine/VM:
record exact edition/version/build/architecture and verify Python is absent
(Installed apps plus command discovery; Store aliases alone are not installed
Python). Do not install Python for this check. Extract the entire ZIP to a
writable local folder, keeping `_internal` intact. Follow only these three checks:

1. In PowerShell inside the extracted `Ravel-workbook` folder, run
   `.\Ravel-workbook.exe --port 8095` (use an unused port if needed). Open
   `http://127.0.0.1:8095/`, choose **Create from scratch**, then **New table**
   and **value**. Expect the workbook/local assets to load.
2. Set Minimum **200** and Apply: expect a complete range error and no applied
   change. Correct to **5**, Apply and **Save configuration**. Change Minimum
   again; **Reload configuration** using the native chooser and saved JSON.
   Expect Minimum **5** restored.
3. Press **Ctrl+C** in the server terminal; expect the prompt to return. A fresh
   HTTP request must fail and the port must no longer have a listener:

   ```powershell
   Get-NetTCPConnection -State Listen -LocalPort 8095 -ErrorAction SilentlyContinue
   ```

Report the environment/Python-absence evidence and pass/fail for those three
checks, including error text. A loaded browser tab alone does not prove shutdown.
No physical-offline, other-platform, benchmark, generation/clinical or release
acceptance follows from this preparation. The [progress record](progress.json)
contains the required next action. Documentation-only follow-up checks cover
tracking, links/image paths, command syntax, dashboard freshness and whitespace;
application/browser checks are reused because no executable source changed.

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

The [README](../README.md) introduces Ravel's purpose, two intended workflows,
current fixture workbook and quickstart. Optional presentation check: view it
in a Markdown renderer and expect one theme-appropriate Ravel lockup, one actual
Dark workbench image, compact rules/example
workflows, explicitly planned generation, license and AI disclosure. Follow its
local document/image links; it no longer contains a clinical table or diagram.
The four reference cases remain in the [clinical specification](baseline-specification.md),
and [specification.md](specification.md) defines the accepted recipe architecture.
Those contracts and numeric prerequisites remain separate from presentation;
examples are expectations, not executed outputs or independent validation.
In the dashboard, check filtering, task-link navigation, keyboard expansion and
visible focus after changes that affect those behaviours.

## Contributor and release preparation

Follow [AGENTS.md](../AGENTS.md) and the [plan](plan.md): work in small, reviewable
changes, use invented fixtures, and keep confidential data and credentials out
of version control. Local Codex implements changes; the ChatGPT Project handles
planning and review, and the maintainer accepts results. Critical clinical
choices and important user-facing behaviour require maintainer review.

The approved [MIT license](../LICENSE) is present. Follow
[CONTRIBUTING.md](../CONTRIBUTING.md) for focused PRs, invented data and responsibility
for AI assistance. The [prototype dependency inventory](dependency-licenses.md)
and [notice collection](third-party-notices.txt) preserve inspected package terms
and identify unresolved frontend/native redistribution work. M0-07 is partial;
this preparation does not complete dependency/license review or any release gate.
The [environment and benchmark proposal](decisions.md#proposed-m0-06-environment-and-benchmark-11-october-2026)
requires maintainer review before adoption; the working environment is unchanged. Consult [progress.json](progress.json) for current blockers and the
required next action. The maintainer accepted residual email discoverability in
retained GitHub history; the [decision record](decisions.md) preserves that
acceptance and the earlier findings without claiming complete removal.

## Reviewed branding integration (11 October 2026)

The workbook uses the approved `ravel-mark-32-light.svg` and
`ravel-mark-32-dark.svg` at their native 32 px size. App theme changes update the
image source alongside dark mode without rebuilding the editor. The SVG favicon
uses the browser's `prefers-color-scheme`, independently of the app's Theme
selector; the supplied ICO is the fallback. Both favicon routes precede the
workbook's catch-all route. Required assets are served locally from canonical
`brand/`; the Windows recipe includes the same four files under `_internal/brand`
and rejects incomplete bundles. Artwork, blue accents, validation colours,
configuration logic and layout are preserved.

The README replaces its text title with a theme-appropriate outlined wordmark
lockup and keeps one refreshed Dark workbook image. These actual 1366×657
captures show the sample route with Maximum `20` still a draft:
[Light workbook](images/m0-06-branding-light.png) ·
[Dark workbook](images/m0-06-branding-dark.png).
Older screenshots and their historical evidence remain unchanged.

Verification on the existing Windows host:

- One complete maintained browser run passed all **eight cases** on the integrated
  CPython 3.11.0 / NiceGUI 3.18.0 app, with Playwright 1.58.0 and Chrome
  154.0.8037.98: both routes/themes at 1366×657 and 1280×800, native-size local
  marks, favicon links, validation, drafts, theme preservation, focus, counts and
  canonical save/reload. No external HTTP/WebSocket attempts or page errors.
- A separate **eight-case matrix** checked both routes and app themes against
  light/dark browser colour schemes. All 16×16 SVG favicon pixels match the
  expected palette/geometry; app theme changes preserve both favicon pixels and
  editor drafts. Canonical mark/SVG/ICO HTTP responses match source bytes.
- All **four affected build tests** passed, including rejection of a missing
  favicon. The existing isolated CPython 3.14.8 / setuptools 80.9.0 candidate
  environment built the updated recipe with its explicit candidate lock. Defaults
  and dependency pins remain unchanged. Only the existing optional `tzdata`
  hidden-import warning remains.
- The full **1202-file** bundle was copied and launched from its own folder with
  Python environment variables removed and Windows-only PATH. Frozen import paths
  stay inside the copy; the four brand assets match canonical source bytes.
  Its local asset responses and all **eight branding matrix cases** passed.
  The full maintained suite was run once against the source app; unchanged
  configuration-unit and E33 bundle evidence retain their original scope. Native
  dialogs, physical-offline and clean-machine checks were not rerun or newly
  claimed here.
- Nine tracking tests, dashboard regeneration/freshness, 97 local documentation,
  image and HTML asset links/anchors, and Git whitespace checks passed. Canonical
  artwork, model/fixtures/locks/plan/decisions, historical screenshot bytes and
  E1–E34 evidence/status records were checked unchanged.

Initial ICO routing returned HTML and was corrected before the complete browser
run and final build; the interrupted partial run and superseded build are not
acceptance evidence. The focused draft comparison needed to wait for the draft
indicator before measuring state; the final matrix passed. Raw logs/results,
focused review drivers and binaries remain ignored under
`outputs/branding-integration-2026-10-11/`.
Both owned review ports closed after stopping the servers. Source server output
collected at Ctrl+C shutdown included an asyncio pipe `ConnectionResetError`
(`[WinError 10054]`); this was separate from the passing browser cases.

Native browser-tab visual inspection was stopped by Computer Use because it
could not determine the Windows browser URL confidently enough to enforce its
policy. Native tab appearance under both browser themes remains for maintainer
review; automated favicon pixel checks do not establish native tab inspection.

On 12 October 2026, the maintainer approved the branding shown in PR #6 at
`3db208e86dd147a06942c4cfde5c9edcd1700efa` and authorized its merge. This
acceptance retains E35 browser/capture evidence and does not establish native
tab inspection, adopt NiceGUI or complete M0-06. Broader workbook and environment
review remains open.

Retained visual checks and remaining native-tab review (recorded in progress.json):

1. Launch with the README quickstart and open `/sample` and `/scratch`. Switch
   app themes: expect the approved native-size mark, the existing layout and blue
   controls. On `/sample`, change Maximum to `20` without Apply, then switch
   themes: expect the draft and Sample origin to stay while Settings remains
   `9.8–12.2 · 0% missing`. Compare the actual captures above.
2. In a browser using a Light theme, inspect the tab with the app in Dark; expect
   the graphite/Fichte favicon. In a Dark browser theme, reload a fresh tab with
   the app in Light; expect light ink/Fichte light. The app's selector must not
   choose the favicon. Record actual tab appearance and visual accept/change
   feedback separately from the accepted PR #6 branding. This does not adopt
   NiceGUI or complete M0-06.

Recorded checks from the repository root, against the isolated review server:

```powershell
.\.venv\Scripts\python.exe -m experiments.workbook.bundle_entry --port 8096
.\outputs\workbook-review-env\Scripts\python.exe scripts/check_workbook_browser.py --base-url http://127.0.0.1:8096 --output outputs/branding-integration-2026-10-11/browser-final
python -m unittest discover -s tests -p test_workbook_build.py -v
.\outputs\python314-setuptools-candidate-2026-10-11\build-env\Scripts\python.exe scripts/build_workbook_windows.py --build-lock experiments/workbook/requirements-build-python314-candidate.lock --output outputs/branding-integration-2026-10-11/build-final
```

Use a new build output path on repeat; the recipe preserves existing evidence.
The private clean-Windows review archive described above remains its earlier
tested build and does not contain this integration. No updated private archive
or public binary was published.
## Fichte interface palette (12 October 2026)

PR #6 branding was accepted at `3db208e86dd147a06942c4cfde5c9edcd1700efa`
and merged as `90e5f59de5d3459a70c0654cd9dc07d1d1ec6d7c`. The separate
`ui/fichte-palette` task applies Fichte to the interface through shared tokens
in `workbook.css`. On 12 October 2026, the maintainer accepted the palette in
PR #7 at `220d730a93393ad9f11e0b43b2cbd45fb4d4e009` and authorized readiness
and merge initially after 16:30 Europe/Berlin. The maintainer subsequently
granted an explicit one-time timing exception for immediate PR #7 publication
and merge; the normal window remains for other work. Acceptance reuses the
evidence below and does not complete outstanding native/platform reviews or
adopt NiceGUI.
The artwork, neutral surfaces, layout, validation colours and editor callbacks
remain unchanged.

| Interaction token | Light | Dark |
| --- | --- | --- |
| Fichte action/link/focus/selection edge | `#3A6B57` | `#8DBAA2` |
| Strong hover/pressed text | `#2B5543` | `#B2D6C2` |
| Button background | `#DCEBE3` | `#31533F` |
| Selected row/menu background | `#E0EDE5` | `#2B4036` |
| Hover background | `#CBDED2` | `#354D40` |
| Pressed background | `#B7D1C1` | `#3D5C4B` |
| Browser text-selection ink | `#FFFFFF` | `#1C2026` |

Buttons, links, active tabs, selected rows/menu items and keyboard rings share
the theme tokens. The selected field also has a 3 px inset Fichte edge so its
subtle tint is not the only selection indicator; existing pressed semantics
remain. Explicit hover/pressed styles replace Quasar's generic focus overlay;
keyboard rings remain visible. Help-button hover/pressed borders use Fichte to
keep their boundaries distinct against the new state backgrounds.

Actual 1366×657 app captures retain Maximum `20` as an unapplied draft, Sample
origin, and applied Settings `9.8–12.2 · 0% missing` across the theme change:
[Light workbook](images/m0-06-fichte-light.png) ·
[Dark workbook](images/m0-06-fichte-dark.png).
The README keeps one actual Dark image. Earlier captures and evidence remain
at their original paths.

One complete maintained browser run passed all **eight cases** on the existing
CPython 3.11.0 / NiceGUI 3.18.0 / Playwright 1.58.0 / Chrome 154.0.8037.98
Windows host: both routes/themes at 1366×657 and 1280×800, state text and
boundaries, selection, focus, branding, validation, drafts/theme preservation,
counts and canonical save/reload. No external HTTP/WebSocket attempts or page
errors were observed. Computed contrast minima include the new states:

| Check | Required | Light minimum | Dark minimum |
| --- | --- | --- | --- |
| Text, including hover/pressed/menu | 4.5:1 | 4.76:1 | 4.69:1 |
| Enabled control boundaries, including states | 3:1 | 3.41:1 | 3.42:1 |
| Row/table/tab selection indicators | 3:1 | 5.09:1 | 5.12:1 |
| Browser text selection | 4.5:1 | 6.14:1 | 7.54:1 |
| Keyboard focus | 3:1 | 5.09:1 | 5.12:1 |

Focused checks caught a Dark pressed-state link below 4.5:1 and help-button
state boundaries below 3:1; stronger state text and Fichte state borders fix
those readings. The earlier interrupted partial browser run is not acceptance
evidence. Final captures, validation/focus screenshots and raw measurements
were inspected. Logs/results are retained locally in ignored
`outputs/fichte-palette-2026-10-12/`.

Nine tracking tests, regenerated dashboard freshness, 99 local documentation
links/anchors and whitespace checks pass. The owned source review server was
stopped and port 8096 verified closed. Packaging and dependency pins did
not change; E35 evidence is reused for unchanged logo/favicon and bundle
behaviour. No build was rerun, binary published or native-tab inspection claimed.
The earlier private clean-Windows archive retains its earlier palette. Native
tab inspection remains unrun; M0-06 stays partial, NiceGUI provisional and release
gates unchanged.

Retained visual try-out for the accepted palette:

1. Launch the README quickstart and open `/sample` and `/scratch` in both app
   themes. Inspect Apply and toolbar actions, selected row/table, active tab,
   links, hover/pressed states and Tab focus. Expect coordinated greens, unchanged
   neutral surfaces/layout and distinct red validation messages.
2. On `/sample`, set Maximum to `20` without Apply and switch themes. Expect the
   draft/Sample origin and applied `9.8–12.2` Settings to remain. Set Minimum to
   `200`, Apply, and expect clear errors/focus; correct to `5` and Apply to recover.
   Compare the accepted captures above. Remaining native/platform reviews are
   recorded in `progress.json`'s next action; palette acceptance does not establish
   those checks or release readiness.

Recorded final browser command, with the source app running on port 8096:

```powershell
.\outputs\workbook-review-env\Scripts\python.exe scripts/check_workbook_browser.py --base-url http://127.0.0.1:8096 --output outputs/fichte-palette-2026-10-12/browser-final
```

Palette implementation, verification and review preparation were AI-assisted
with Codex. Logo creation with Claude and its earlier AI-assisted review remain
recorded in PR #6 and the existing branding evidence.

## Workspace ergonomics (13 October 2026)

This bounded task starts from clean `main` at the PR #7 merge
`5b7464a8c2b97219aae4bde19726d02c637663c2`, verified against GitHub.
The maintainer's priority is that visual quality and UX remain acceptance
criteria throughout development. The new interaction requires its own visual
review; M0-06 remains partial and NiceGUI provisional.

Properties defaults to **312 px**. Drag its divider left to enlarge it, or Tab
to the divider and use the keyboard. A visible Fichte grip, focus ring, nearby
guidance and toolbar **Reset layout** make the interaction discoverable.

| Action | Result |
| --- | --- |
| Left / Right | Widen / narrow Properties by 10 px |
| Shift + Left / Right | Adjust by 40 px |
| Home / End | Minimum / maximum Properties width |
| Escape during drag | Cancel that drag and restore its starting width preference |
| Reset layout | Restore the 312 px preference without changing edits |

Properties is limited to **300–560 px**, further constrained by available space.
The central workspace keeps at least **360 px** at the tested laptop sizes;
the existing narrower-width rule uses 320 px below 1100 px. The new divider is
10 px wide, so the default remains close to the accepted arrangement. Table
labels/settings wrap within their columns, origin/draft metadata can wrap, and
Properties continues to scroll for expanded explanations. Apply is reachable
with the keyboard. No full docking, generation or dependency changes are added.

The divider uses a focusable vertical ARIA separator, current/min/max width,
readable value text, a controlled-pane reference and visible help, informed by
the [WAI window-splitter guidance](https://www.w3.org/WAI/ARIA/apg/patterns/windowsplitter/).
There is no collapse action: the minimum keeps Properties usable. This is not
a screen-reader or complete accessibility audit.

Ctrl/Alt/Meta arrow shortcuts are not consumed by the divider; resizing uses
the documented unmodified/Shift keys.

Layout width belongs to the current workspace DOM. Resizing/reset does not
replace editor controls or call model validation/application. It survives app
theme and Fields/Preview changes, and is absent from saved configuration JSON.
Opening a new page or replacing the workbook through JSON reload starts at the
default width; this is presentation behaviour, not a recipe format change.

Actual sample-app captures use the same Maximum `20` draft, applied
`9.8–12.2 · 0% missing` Settings and Sample origin. Before is the accepted
312 px layout; after has Properties enlarged to 480 px:

| Theme | Before | After |
| --- | --- | --- |
| Light | [Actual before](images/m0-06-ergonomics-before-light.png) | [Actual after](images/m0-06-ergonomics-after-light.png) |
| Dark | [Actual before](images/m0-06-ergonomics-before-dark.png) | [Actual after](images/m0-06-ergonomics-after-dark.png) |

The README keeps one actual Dark image of this interaction. Historical captures
and their evidence remain unchanged. Additional 1280×800, error, focus and
long-name captures are retained locally in ignored
`outputs/workspace-ergonomics-2026-10-13/`.

Verification on the existing Windows host:

- A four-case before walk covered field editing, distinct draft/applied origin,
  theme preservation and range recovery at both laptop sizes and themes.
- **One complete maintained browser run passed all eight cases** on CPython
  3.11.0 / NiceGUI 3.18.0 / Playwright 1.58.0 / Chrome 155.0.8059.40: both routes,
  themes and 1366×657 / 1280×800 viewports. Added assertions exercise drag,
  keyboard/Shift steps, limits, cancellation, Reset layout, valid/invalid edit
  preservation, view/theme changes, visible errors/essential controls and
  byte-identical JSON after resize. Existing validation, immediate focus,
  provenance, counts, branding and canonical save/reload assertions passed.
  No external HTTP/WebSocket attempts or page errors were recorded.
- Focused checks covered a 38-character invented field name at maximum width,
  pointer limits, unaltered JSON and keyboard access to Apply with Assumptions
  expanded. The initial stress fixture exceeded the existing 40-character name
  limit and was shortened before the final checks; it was not an app failure.
- Minimum Light/Dark contrast: text **4.76 / 4.69**, enabled boundaries
  **3.41 / 3.42**, selection/focus **5.09 / 5.12**. New divider grip contrast
  across normal/hover/drag states is at least **3.77 / 3.42**. All meet the
  existing 4.5:1 text and 3:1 boundary/selection/focus requirements.
- Nine tracking tests, dashboard freshness, 103 local documentation links/anchors
  and Git whitespace checks passed. The owned review server is stopped after
  verification. A preceding maintained run passed before final keyboard review
  added the modifier guard; its raw results are retained, with the final run in
  `browser-final-reviewed/`. The model, fixtures, clinical contracts, accepted
  palette/artwork, locks and packaging recipe remain unchanged. E35's unaffected packaging
  evidence is reused within its original scope; no updated bundle was built or
  published. Native tab/dialog/keyboard, screen-reader, clean-machine,
  other-browser/platform and broader environment reviews remain outstanding;
  release gates are unchanged.

Required maintainer try-out is recorded in `progress.json`'s next action:

1. Launch the README quickstart; inspect `/sample` and `/scratch` at both laptop
   sizes in Light and Dark. On `/sample`, change Maximum to `20` without Apply.
   Drag left to widen Properties: expect the same selected field, Sample origin,
   Draft marker and applied `9.8–12.2` Settings, with readable controls and messages.
2. Tab to the divider and check its visible focus. Try arrows, Shift, Home/End
   and Reset layout; expect the widths above and unchanged edits. Switch themes
   and Fields/Preview; the chosen width and editor state must survive.
3. Set Minimum to `200`, Apply, then resize/reset and switch views/themes. Expect
   complete errors and retained drafts. Correct Minimum to `5`, Apply and
   save/reload JSON. Expect Edited origins for applied overrides and no layout
   setting in the file; JSON reload starts with the default layout. Compare the
   actual captures and record accept/change feedback. Keep the new PR draft
   and unmerged for review.

Recorded maintained check against the isolated source server:

```powershell
.\outputs\workbook-review-env\Scripts\python.exe scripts/check_workbook_browser.py --base-url http://127.0.0.1:8096 --output outputs/workspace-ergonomics-2026-10-13/browser-final-reviewed
```

Implementation, interaction/contrast checks, captures and documentation were
AI-assisted with Codex. Local preparation was left uncommitted during the Berlin
restricted window. On 13 October 2026, the maintainer explicitly authorized
immediate publication of this task as a separate timing exception. The PR stays
draft and unmerged for visual/UX review; the normal window remains for other work.

### Viewport width regression repair (15 October 2026)

Claude's **reported Linux review**, supplied by the maintainer, identified lost
Properties width after viewport narrowing and restoration on PR #8's reviewed
head `abcfb5c50e9591e43e37ac733316ab1bd8d78a0c`. This is attributed review
evidence, separate from the Windows observations below. No Linux rerun or Linux
suite result is claimed here.

Before editing, Codex independently reproduced **560 → 446 → 446** in Windows
Chrome 155.0.8059.40: at 1366×657 choose End (560 px), narrow to 900 px, then
restore 1366 px. A fresh 760×657 page rendered 306 px while its untouched ARIA
current/max were incorrectly 312/560. Raw reproduction JSON and capture are in
ignored `outputs/viewport-resize-2026-10-15/`.

The inline CSS width now retains the user's preference while CSS constrains the
rendered width. Viewport changes never write the rendered width back into that
preference. A ResizeObserver synchronises ARIA from actual layout, observing the
grid and Properties pane; it is installed after Vue renders the initial shell
and each valid JSON workbook replacement. The previous observer is disconnected
on replacement. Focus is not required to initialise metadata. Reset restores
the 312 px preference even when only 306 px can render. Drag start records both
rendered width and preference, so Escape and pointer cancellation restore the
pre-drag preference even when it was temporarily constrained.

The maintained browser script adds focused assertions for the exact resize
sequence, untouched fresh-page ARIA at 760 px, constrained Reset, Escape and
pointercancel with 480/560 px preferences in wide/constrained windows, retained
input identities/drafts/errors/selection/applied settings, byte-identical saved
JSON after layout operations, and valid reload from 480 px back to the default.
Both original laptop viewports, entry paths and themes retain their existing
checks. Pointer cancellation is dispatched by the harness after a real mouse
drag; this does not establish native touch-device cancellation behaviour.

Final maintained run command (existing Windows runtime and review environments):

```powershell
.\outputs\workbook-review-env\Scripts\python.exe scripts/check_workbook_browser.py --output outputs/viewport-resize-2026-10-15/browser-final
```

All **22 unit tests** passed (nine tracking, nine configuration and four packaging
recipe tests with mocked build subprocesses). The affected Markdown documents'
61 local file links resolve, and Git whitespace checks passed. No new packaging
build is implied by the recipe unit tests.

Exactly **one complete maintained browser run** against the final Windows
implementation passed all **eight cases**: CPython 3.11.0, NiceGUI 3.18.0,
Playwright 1.58.0 and Chrome 155.0.8059.40 headless on the existing Windows
build 26300 host. All new regression assertions and existing checks passed.
Browser HTTP/WebSocket and owned server socket/DNS guards recorded zero external
attempts; no browser page errors or server stderr diagnostics were observed.
The focused final capture was inspected. The dashboard was regenerated and
passes freshness plus all nine tracking tests after the progress update. The
owned server was stopped after verification.

Maintainer try-out procedure retained for reproducibility; acceptance is recorded
below:

1. Launch the README quickstart. On `/sample` at 1366×657, Tab to the divider
   and choose End. Narrow to 900 px and restore: expect **560 → 446 → 560**.
   Repeat with an unfinished Maximum `20` and invalid Minimum `200`; selection,
   Draft markers, errors and applied Settings must survive.
2. Open a fresh workbook at 760 px before focusing the divider. Its rendered
   width and ARIA current/max must be **306/306/306**. Reset while constrained,
   then widen: expect the **312 px** preference. With a 560 px preference
   constrained at 900 px, start a drag and Escape; widening must restore 560 px.
3. Save valid JSON, widen Properties to 480 px, then reload with the native
   chooser. Expect default 312 px and unchanged configuration content. Review
   both themes/routes and original laptop sizes using the earlier captures;
   record accept/change feedback.

Unaffected E35 packaging evidence is reused within its original scope. No bundle
was rebuilt; runtime/build locks, packaging recipe, model, fixtures and clinical
rules are unchanged. Native chooser/touch/screen-reader, clean-machine and other
platform checks remain outstanding. M0-06 stays partial and NiceGUI provisional.

### Workspace maintainer acceptance (15 October 2026)

The maintainer reports checking and accepting the locally fixed PR #8, including
viewport resizing, draft preservation, Reset layout and theme/Fields-Preview
switching. Acceptance includes the uncommitted viewport repair on
`ui/workspace-ergonomics` based on
`abcfb5c50e9591e43e37ac733316ab1bd8d78a0c`, rather than only that published head.
This supersedes the pending workspace try-out above; it does not claim checks
outside the maintainer's reported scope.

Before recording acceptance, Codex compared the app and maintained browser-check
sources with cached Python code written before E41's browser run. Both match,
and both source/cache modification times precede the recorded run start. Their
SHA-256 values are recorded in E42. Application/check sources are unchanged by
this acceptance update, so E41's eight Windows browser cases and existing unit
evidence are reused. Claude's reported Linux finding remains separately
attributed in E40. Unaffected E35 packaging evidence retains its original scope;
no new app/browser/build or binary-publication claim is made.

The maintainer authorizes committing the fix and acceptance documentation with
the established noreply identity, pushing, marking PR #8 ready and merging with
a merge commit under branch protection, then synchronising local main. These
actions are pending until after **16:30 Europe/Berlin on 15 October 2026**, with a
fresh live-clock check immediately before each commit or GitHub write. Local
preparation is saved uncommitted during the restricted window; publication is
neither scheduled nor performed early. The existing progress record carries the
publication handoff and the subsequent separate Windows preview build environment
selection task. No environment or distribution decision is adopted here. M0-06
remains partial, NiceGUI provisional and all release gates unchanged.

Acceptance preparation passed all nine tracking tests, dashboard regeneration
and freshness, 64 affected local documentation links/anchors and evidence
references, and Git whitespace checks. Accepted source hashes, historical
evidence and task/milestone/gate preservation were checked. Valid application,
browser and packaging evidence was reused for unchanged code; those runs were
not repeated for this acceptance update.

### Publication authorization (16 October 2026)

The maintainer reaffirms acceptance of the locally fixed PR #8 and explicitly
authorizes committing, pushing, readiness, merge under branch protection and
main synchronization during the usual restricted Berlin period for the current
publication batch. The normal 08:00-16:30 Europe/Berlin rule remains for subsequent
work, and a live Berlin clock is checked immediately before every commit or
GitHub write. E42 and its accepted source hashes remain unchanged. This timing
authorization and maintainer report are distinct from automated verification;
no broader native, installation or release acceptance is implied.

### Single-table maintainer acceptance (16 October 2026)

The maintainer reports testing the current app and that everything works fine.
E46 records acceptance against the saved local generator version: all 15 files
in the 09:34 tested-source manifest still match, with runtime source hashes
recorded in that evidence. No generator runtime source changed for acceptance.
This report is separate from the automated E44/E45 results and does not claim
specific native chooser, every-theme/viewport, installation or clean-machine
checks beyond what the maintainer reported. The new PR remains draft and
unmerged for joint code review. PR #8/E42 acceptance stays separate.

An additional dependency-free CPython 3.14.8 x64 environment (no pip or NiceGUI)
passed all 41 tests and dashboard freshness. An initial attempt encountered
sandbox temporary-folder permissions; a task-local writable temporary directory
resolved that environment problem. Five literal-category edit/Apply/save-reload
checks preserved CR, LF, CRLF, quotes, commas and Unicode. No product change was
required. Hosted core CI remains pending execution, and this local check is not
native installation evidence. M0/full M1 and release gates remain incomplete.

### Recipe-size and focus repair (17 October 2026)

E49 records the saved-size boundary repair: canonical UTF-8 recipes must fit
within the same 1 MiB bound before Apply/load accepts them. A compact recipe
that expands beyond that size now fails clearly while preserving current state.
Two new regression methods reproduce direct/upload/save and atomic duplication
failures; the suite now has 43 tests. The earlier E46 human acceptance remains
attached to its recorded sources and does not silently accept later changes.

Visual checking caught a screenshot race; capture now awaits actual Preview.
Further final runs exposed premature keyboard navigation and an actual focus
loss during rule refresh. Selector blur is awaited and the target control is
not blurred before focus. The maintained browser checks explicitly await the
documented post-action focus. The final 17 October run passes all four themes/
laptop cases, with no page errors or external browser HTTP/WebSocket attempts.
Actual Dark fields and Light generated captures were inspected. Earlier failed
runs remain retained separately; no arbitrary delay or weakened assertion was
used. Fichte CSS, layout JavaScript and headless generation are unchanged.

Hosted push/PR core runs at `709966be3503ea5c39edc9f13a117feea4138c8c` each
passed 41 tests, dashboard freshness and whitespace on Windows/Linux/macOS
(E48). These precede E49; no hosted result is claimed for an unpushed repair.
PR #10 remains draft and unmerged. The normal Berlin publication rule applies
to the newly authorized sequential issue #11 queue; no new merge or binary
publication is authorized. M0/full M1 and release gates remain incomplete.

### Sample workflow (17 October 2026)

Issue #12 is implemented locally on the repaired generator baseline. See
[sample-assisted.md](sample-assisted.md) for the contract, invented references
and UI/CLI walkthrough. Eleven new tests bring the full local suite to 54.
The final Chrome run passes eight cases: both workflows at Light/Dark and
1366×657/1280×800, including keyboard recovery, actual output/CSV and source
retention, reproducible recipe reload, and the existing layout regressions.
Use the maintained runner against an isolated development server:

```bash
python scripts/check_generator_browser.py --base-url http://127.0.0.1:8096 --workflow all --output outputs/sample-browser
```

The initial new browser assertion counted a hidden source table as output;
the corrected selector checks the actual preview only. Failed attempts are
retained separately. Current screenshots show the actual imported source and
retained/generated output, not illustrative data. The import preview feels
cramped at the shorter laptop height; the next UX package addresses that.
Tests use Python3.14.8/NiceGUI3.18.0/Playwright1.58.0 and Chrome155.0.8059.82
on this development host. No page errors or browser external HTTP/WebSocket
attempts were observed. E50 records scope; E46 remains earlier human acceptance.
No new hosted CI, native chooser, clean-machine or release claim is made.
