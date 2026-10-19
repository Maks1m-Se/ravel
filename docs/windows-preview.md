# Private Windows preview

This is an unsigned, unaccepted development preview of the current Ravel app.
Keep it private while artifact-specific redistribution findings and a clean
Windows review remain open. It includes the Python runtime; an installed Python
is not intended to be required. Actual development-host execution does not prove
that claim on a machine without Python. No installer, updater or public release
is provided.

Extract the **whole** ZIP into a new writable folder. Do not move Ravel.exe away
from `_internal`. Read `source-version.json` for the exact content version and
source hashes, `manifest.json` for the actual included files and SHA-256 values,
and the adjacent `SHA256SUMS.txt` to check the ZIP before extraction. A content
snapshot may record an earlier Git base plus dirty state; the complete declared
source hashes, not an invented commit label, identify that candidate.

## Start, use and stop

On the tested Windows x64 host, open PowerShell in the extracted Ravel folder:

```powershell
.\Ravel.exe ui
```

Open http://127.0.0.1:8090/ in Edge or your usual browser. If that port is busy,
use ` .\Ravel.exe ui --port 8102` and open http://127.0.0.1:8102/ instead. A
double-click starts the same default local workbench. Keep the console open.
Stop with Ctrl+C in that console, then close the browser tab. Verify the chosen
port closes. Browser tabs may remain visible after the server stops.

No administrator rights, network service or Python installation should be
needed. The server binds loopback only and does not open the browser automatically.
Do not disable SmartScreen, Smart App Control or Defender. Record any normal
protection warning/block, its text and the candidate checksum for review.

Use explicit rules to generate1,000 rows, edit/add/duplicate fields, inspect the
real Preview, export CSV and save/reload. Import the invented ten-row CSV under
`_internal/examples/sample-assisted/ten-rows.csv`: inspect/edit assumptions,
confirm identifiers, then generate1,000 new rows or extend to1,000 total with
originals retained and row_origin recorded. Try the extended-rule recipe and
Home > Use template > Devices / measurements; expect three devices and six
measurements, then review a changed child count and export the complete ZIP.
Invalid/unapplied edits and stale results must prevent export without losing
the previous valid state. Save important work before closing; sessions are in memory.

The same executable supports the CLI; choose fresh output paths:

```powershell
.\Ravel.exe validate .\_internal\examples\linked\devices-measurements.recipe.json
.\Ravel.exe generate .\_internal\examples\linked\devices-measurements.recipe.json --directory .\devices-review
```

This preview is generic. The clinical preparation documents/reference sheets
are not a clinical generator or an available clinical template. See
`NOTICES-REVIEW.md`, `THIRD-PARTY-NOTICES.txt`, `notices/`, and the included
corresponding-source archive/material before considering distribution.

## Build selection and repeatability

For this bounded private candidate select standard CPython3.14.8 Windows x64
with the GIL, the unchanged `requirements-ui.lock` and separate
`requirements-windows-build.lock`. This makes a binary-build selection; prior
source adoption alone was insufficient. The setuptools80.9.0 isolated candidate
had resolved the recorded3.14 import problem. Old experiment locks stay unchanged.
On18October2026 the official [Python3.14.8 release](https://www.python.org/downloads/release/python-3148/)
provides Windows x64 binaries; [NiceGUI3.18.0 metadata](https://pypi.org/project/nicegui/3.18.0/)
and [PyInstaller6.20.0 documentation](https://pyinstaller.org/en/v6.20.0/)
support the selected interpreter series. Actual isolated candidate execution is
the additional local evidence; this is not an all-platform support claim.

From a checkout, use a bootstrap interpreter with pip, prepared pinned wheels
and fresh environment/output directories:

```powershell
python scripts/prepare_windows_preview_environment.py --output .\outputs\preview-env --wheelhouse C:\path\to\wheels
.\outputs\preview-env\Scripts\python.exe scripts/build_windows_preview.py --output .\outputs\preview-build --source-material C:\path\to\prepared-sources
```

The environment tool uses `venv --without-pip`, installs the exact two locks
offline with the bootstrap pip, checks dependencies and requires the installed
distribution inventory to match exactly. Review/browser tools and pip itself
do not enter the build venv. The builder repeats that check, directly invokes
PyInstaller with a checked exit code and builds the current CLI/UI entrypoint.
It snapshots/compares declared inputs, retains build logs/analysis components,
copies actual supplied notices, stages the complete folder, generates the actual
manifest and creates the ZIP/checksum. It never reuses an old experiment output
or overwrites an existing build folder. A failed build remains evidence; it is
not a successful candidate. Source material has a separate recorded URL/hash map.

Rebuild from unchanged declared inputs and exact pins in a new environment/output.
Compare declared source/input hashes, component inventory and output path set,
then validate each artifact's own hashes. PE/bytecode/build-path timestamps can
change output bytes; bit-for-bit executable/ZIP reproducibility is not claimed.
The comparison tool must report changed bytes rather than conceal them.

The complete source-material procedure is tracked as well. Build a bootstrap
folder without `--source-material`, then run `audit_windows_preview.py` against
that actual folder. The optional font parser can be installed separately with
`requirements-license-review.lock`; never add it to the build venv. Prepare
the pinned Python sources with `collect_windows_preview_sources.py --output DIR`,
then `enrich_windows_preview_sources.py --material DIR --asset-audit AUDIT_JSON
--output NEW_DIR`, and `collect_windows_frontend_sources.py --material NEW_DIR
--bundle BOOTSTRAP_FOLDER --output FINAL_MATERIAL`. Each accepts explicit fresh
paths. npm archives are checked against the tagged lock's SHA-512 integrity;
source URLs/SHA-256 and supplied texts are retained. A deliberate `--resume`
rechecks every cached archive and preserves the preceding source-index version.
Build the final candidates with `--source-material FINAL_MATERIAL`.

Verify actual frozen CLI/imports with `check_windows_preview.py --bundle FOLDER
--output NEW_DIR`, and the real packaged UI/console lifecycle with
`check_windows_preview_server.py --bundle FOLDER --output NEW_DIR --port 8102`.
The latter owns a hidden test console, runs all16 Chrome cases and one Edge
case, uses the actual EXE for CLI comparisons, sends a console Ctrl+C event and
checks process/port closure. It refuses manual-review ports8100/8101. Run
`compare_windows_previews.py FIRST_FOLDER SECOND_FOLDER --output REPORT_JSON`
after a clean second build. Stable file bytes and corresponding-source ZIP
contents must match; known ZIP containers must also have byte-identical decoded
members. Executable/ZIP container variability is
reported separately. Actual native keypress/file-picker/clean-guest checks remain
the manual checklist below.

## Clean-Windows review checklist

No clean guest/second Windows computer without Python is currently available.
All checks below require actual evidence on an authorized clean environment;
hosted core tests and development-host browser interception do not satisfy them.

| Record / check | Required evidence |
| --- | --- |
| Environment | Edition, display version, exact OS build, x64 architecture, language, standard-user status; absence of Python/package tools, PATH and installed-app evidence |
| Artifact | ZIP filename/SHA-256, extraction path, source content version, complete manifest validation before launch |
| Protections | Defender engine/signature versions and real-time status, Smart App Control state, SmartScreen/default-browser settings; timestamped actual prompts/blocks, with protections retained |
| Start | Extract/start without admin or Python, default port and alternate-port behavior, Edge and actual default-browser opening, readable console errors/URL |
| Functional | Explicit1,000-row workflow; ten-row sample new/extend/originals/origin; extended-rule failure/recovery; linked3+6 fixture/all exports; save/reload/reproduce |
| Native files | Real Windows file picker, upload Cancel, Unicode/spaced path, actual downloaded CSV/recipe/ZIP opening, existing-file preservation, native browser save/open behavior |
| Laptop/keyboard | Light/Dark at1366x657/1280x800, Tab/focus, Properties arrows/resize, dialogs/errors/stale export and comfortable controls |
| Offline | Physically disconnect or disable the guest adapter before cold start; both entry paths, files and template work without external requests; distinguish this from browser request interception |
| Shutdown/restart | Ctrl+C closes loopback port/process, tabs handle stopped server, restart reclaims port, no lingering child service; extracted read-only/unwritable location yields clear errors where relevant |
| Result | Actual pass/fail/not-run per item with timestamp/log/capture and exact candidate; maintainer acceptance recorded separately |

Native installation, Windows ARM, other platforms, screen-reader/touch behavior,
all R3/R5/R10 gates and release acceptance remain outside the completed source
checks. Artifact-specific observations belong in progress.json and the generated
dashboard, with their concrete pending items preserved.
