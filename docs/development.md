# Development guide

Runnable tooling includes a read-only progress dashboard using Python's standard
library and a bounded NiceGUI workbook interaction experiment. Production
generation and the application CLI/UI are not implemented. The experiment's
dependencies and provisional configuration do not establish an application API.

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

The compact workbench has a Light/Dark selector, fixed panes and Fields/Preview
tabs. Badges beside each setting show the applied origin: **Default**, **Sample**
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

The [README](../README.md) introduces the project; the
[clinical specification](baseline-specification.md) is the source for its four
reference cases, and [specification.md](specification.md) defines the accepted
recipe architecture. The clinical contracts and numeric prerequisites remain
separate from presentation changes. Examples are specification reference
expectations, not executed application outputs or independent clinical validation.

Optional presentation check: view the README in a Markdown renderer with
Mermaid support. Expect four case rows with baseline/change pairs 10/+3, 8/+3,
null/null and 10/+5, plus one diagram explicitly labelled as planned architecture.
Follow the local document and license links. This checks presentation and links,
not clinical correctness. In the dashboard, check filtering, task-link navigation,
keyboard expansion and visible focus after changes that affect those behaviours.

## Contributor and release preparation

Follow [AGENTS.md](../AGENTS.md) and the [plan](plan.md): work in small, reviewable
changes, use invented fixtures, and keep confidential data and credentials out
of version control. Local Codex implements changes; the ChatGPT Project handles
planning and review, and the maintainer accepts results. Critical clinical
choices and important user-facing behaviour require maintainer review.

The approved [MIT license](../LICENSE) is present. M0-07 still requires the
remaining contributor/release rules and dependency/license review before public
alpha; adding the license and this guide does not complete the task or any
release gate. Consult [progress.json](progress.json) for current blockers and the
required next action. The maintainer accepted residual email discoverability in
retained GitHub history; the [decision record](decisions.md) preserves that
acceptance and the earlier findings without claiming complete removal.
