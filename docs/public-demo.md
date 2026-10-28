# Public Ravel demo

[Open the demo](https://ravel-personal-test.onrender.com/).

The maintainer authorized public access and publication during the vacation
period. This is a small, session-only demonstration of the generic workbench,
not an accepted release or a public Windows download. The existing draft PRs
remain unmerged. The source is on `deploy/render-personal-weekend`.

## Use and limits

No login is required in public mode. Use invented data only: imported CSVs and
recipes, including embedded samples, are processed on the shared server. Each
page has its own Workspace; there are no accounts, saved projects or private
storage guarantees. Download your recipe and CSV/ZIP before closing or reloading.

- At most 1,000 rows across all tables and 20,000 cells per generation.
- Imported CSV: at most 1,000 source rows and 1 MiB; recipe files: at most 1 MiB.
- One process permits two simultaneous generations and 30 starts per minute.
  A busy response preserves the recipe so the user can retry.
- Oversized HTTP upload bodies are rejected before NiceGUI processes them.
  Foreign-origin requests and WebSocket handshakes are rejected.

These are workload bounds for a small demo, not a denial-of-service guarantee.
The local CLI retains its original limits. Render Free can sleep after 15 idle
minutes; an initial request can take about a minute. Restarts lose session state.
No paid plan, database, persistent disk, keepalive or uptime commitment is added.
See [Render's Free service limits](https://render.com/docs/free).

## Compact controls

The top-right **More options** (`…`) menu contains Light/Dark, Reset layout and
Session help. Changing the theme preserves edits and generated data. Escape
closes the menu and returns focus to its trigger. Help icons are smaller while
retaining focus/tap access. Labelled inputs reserve space below their values.
Add, Duplicate and Remove column use icons with accessible names and tooltips;
removal still requires confirmation. No extra speculative actions were added.

Actual local captures: [Light menu](images/compact-controls-light.png),
[Dark pending edits](images/compact-controls-dark.png),
[short mobile import](images/public-demo-mobile-import.png).

## Operation

- Service: `srv-dbdhvi59fdbs73b6rm40`, `ravel-personal-test`, Frankfurt, Free.
- [Render dashboard](https://dashboard.render.com/web/srv-dbdhvi59fdbs73b6rm40).
- Branch: `deploy/render-personal-weekend`; automatic deploys disabled.
- Python 3.14.8; unchanged `requirements-ui.lock`.
- Build: `python -m pip install -r requirements-ui.lock && python -m pip check`.
- Start: `python -m ravel.web`, bound to `0.0.0.0:$PORT`, no reload.
- Public mode requires exactly `RAVEL_PUBLIC_DEMO=1`. Missing/`0` retains the
  personal credential requirement; other flag values fail startup.
- Existing authentication secrets are retained in Render only. Setting the
  flag to `0` and redeploying restores the personal gate. Do not print secrets.
- The existing service uses Render's TCP health check; `/healthz` is verified
  separately. The Blueprint requests `/healthz` for future provisioned services.

The current live implementation is
[`79e44cb405033aa16e8459c59903c3120643656d`](https://github.com/Maks1m-Se/ravel/commit/79e44cb405033aa16e8459c59903c3120643656d),
deploy `dep-dbh0u26i0phs73aeeh90`, live since 28 October 2026, 16:05:50 Berlin.
It contains both source/provenance limit repairs and passed the five-case HTTPS
checker. Later documentation-only commits do not require another deployment.

The previous protected deployment is `d58e977ab2cac654c5012918e35b26fc899ab0f4`,
deploy `dep-dbdhvit9fdbs73b6rnv0`. The first public deployment was
`ac176403633e49c605f7295690c613c6db25afa4`, deploy
`dep-dbg84v0m7kps73bmfg2g`, live since 27 October 2026, 11:53 Berlin.
The environment update itself triggered that deployment; no duplicate trigger
was sent. The service remains Free with automatic deployments disabled.

The initial 27 October HTTPS pages/health and same-origin WebSocket opening passed; foreign
Origins returned403 and oversized HTTP upload bodies413. The cloud-browser
check opened the actual public site, changed Dark to Light while retaining a
Maximum20 draft, applied it, generated1,000 rows and downloaded CSV/recipe.
The CSV has1,000 sequential IDs and every value is within0–20; Discard restored
20 after editing30 and re-enabled the current export. A fresh public session
uploaded the invented ten-row CSV and displayed the correct three-column profile
and identifier rule from11. That hosted sample test stopped at the review
dialog; full sample generation/isolation/mobile coverage is local evidence.
[Actual live capture](images/public-demo-live.jpg).

Both initial GitHub workflows passed. The [PR workflow](https://github.com/Maks1m-Se/ravel/actions/runs/40491959122)
ran unit/dashboard/whitespace checks successfully on Windows, macOS and Ubuntu.
The initial standalone hosted browser harness could not complete in its execution
environment: direct Chromium gave ERR_EMPTY_RESPONSE; using the configured
proxy gave ERR_CERT_AUTHORITY_INVALID. HTTPS verification was not disabled.
The separate cloud-browser checks above succeeded. Actual Pixel/Gboard and
visual acceptance remain pending.

## PR25 technical review (27–28 October 2026)

Review baseline: PR25 head `fb800744c7a5e201d4b89d49613d468be5745d66`.
Isolated branch `review/pr25-technical-2026-10-27` lives at
`C:\Git\ravel\outputs\pr25-review\worktree`. The main checkout and the saved
recovery/staged worktrees are preserved. No new Render service, configuration
change or deployment was made for this review.

Two confirmed hosting-limit defects are corrected locally:

- Sample generation now counts the added `row_origin` column toward the
  20,000-cell limit. Nineteen source columns at 1,000 rows produce exactly
  20,000 cells; twenty would produce 21,000 and must be refused.
- A recipe with an embedded sample now obeys the same 1,000-source-row bound
  as CSV import. An oversized embedded source is refused before replacing the
  current workbook, preserving its result and pending edits.

The core engine and local CLI retain their original limits. New regression tests
failed on both defects before the repair. The final local public browser run
passes five cases, including both themes, mobile emulation, downloads, import,
session isolation and the two limit boundaries with recovery to 19,950 cells.
Both fixes are now deployed in `79e44cb`, as identified above and verified below.
All 96 unit tests, regenerated dashboard freshness and whitespace checks pass.

The existing HTTPS service passed the full original public checker on
27 October with Chrome156.0.8078.48, Python3.14.8 and NiceGUI3.18.0 on Windows:
anonymous HTTP, same-origin WebSockets, foreign-Origin/oversized-body rejection,
both compact desktop/mobile workflows, 1,000-row CSV and recipe downloads,
complete invented-sample import/generation and two independent contexts.
There were zero page errors. This fills the earlier hosted sample/isolation/
mobile-emulation gaps; an actual Pixel/Gboard test remains unrun.

An initial local run failed the menu trigger's post-theme focus assertion.
It was not reproduced by the final complete local run; no focus correction is
claimed. The earlier 24-case layout matrix remains E63 evidence and was reused
for unchanged layout. Raw results, failed runs and original-file hashes are
retained under `C:\Git\ravel\outputs\pr25-review`.

On 28 October the full desktop matrix was repeated on the repaired source:
all 24 cases pass, with no page errors or external HTTP/WebSocket attempts.
The repeated public checker passes all five cases and all 96 units pass
again. Both local servers stopped; `pip check`, dashboard and whitespace
checks pass. The public server log retains two Windows Proactor connection-
reset diagnostics despite passing browser checks. Subsequent publication used
the maintainer's explicit current-day exception and confirmed workspace, as
recorded below; no publication was scheduled.

## Published repair verification (28 October 2026)

The maintainer explicitly confirmed publication before 16:30 Berlin on this day
and workspace `tea-ctkuvolds78s73c2u1j0`. Live clock checks immediately before
the implementation commit and push were 16:03:53 and 16:04:07 Berlin.
All 13 committed runtime files matched the tested files after LF normalization.
The existing Free/Frankfurt service, one instance, manual deployment policy and
secrets were preserved. A single manual trigger deployed `79e44cb`; Render
returned `live` at 15:05:50 UTC / 16:05:50 Berlin. No PR merge or new service.

Actual `outputs/pr25-review/hosted-79e44cb/results.json` records five passed
HTTPS cases with Chrome156.0.8078.73, zero page errors and independent contexts.
Anonymous HTTP/health, same-origin WebSocket, rejected foreign Origins and
oversized requests, both themes, portrait/landscape/reduced-height workflows,
Apply/Discard, generation, recipe/CSV download and full invented CSV import pass.
The actual deployed guards accept exactly 20,000 output cells, reject 21,000,
recover at 19,950, and reject a saved recipe with 1,001 source rows while
preserving the prior workbook and drafts. No TLS verification was disabled.
Actual hosted captures: [pending edit](images/public-demo-repair-live.png),
[reduced-height import](images/public-demo-repair-mobile.png).

An independent read of downloaded files verifies IDs1–1000 and values0–20;
sample IDs11–1010, ranges/categories and `generated` origins; 1,000 rows ×20
columns and 950 rows ×21 columns at the cell boundaries. File hashes are in
`independent-artifact-verification.json` beside the raw browser report.
Render returned no error-level logs for the post-trigger verification interval.
The new [PR CI run](https://github.com/Maks1m-Se/ravel/actions/runs/40712206277)
passes 96 tests plus dashboard/whitespace on Ubuntu and Windows; macOS was still
queued at readback and is not claimed passed. Actual Pixel/Gboard and subjective
maintainer acceptance remain open.

## Verification and required try-out

With the source/review dependencies from `development.md`:

```sh
python -m unittest discover -s tests -v
python scripts/check_personal_web.py --desktop --output outputs/compact-desktop-new
python scripts/check_public_demo.py --output outputs/public-demo-new
python scripts/check_public_demo.py --base-url https://ravel-personal-test.onrender.com --output outputs/public-demo-hosted-new
python scripts/build_dashboard.py --check
git diff --check
```

Browser checks default to installed Chrome. `--executable-path /path/to/chromium`
selects an explicitly recorded alternative. Use fresh output directories. The
local commands own and stop their server; no manual review instance is touched.
The public checker checks real HTTP/WebSockets, upload limits, theme/menu/input
geometry, error recovery, 1,000-row generation, CSV/recipe downloads, sample
import and two independent contexts. Mobile emulation covers portrait, landscape
and reduced height; it cannot establish actual Android/Gboard behavior.

Required maintainer try-out on the live URL:

1. Open `…`, change Light/Dark, close with Escape or a tap outside. Confirm the
   controls feel clear and the input values have comfortable vertical spacing.
2. Change Maximum to 20, switch themes and Apply. Change it to 30 and Discard;
   expect 20. Generate and download the CSV and recipe.
3. Try Add/Duplicate/Remove, cancelling removal once. Hover or focus the desktop
   controls to identify them. On the phone, check the touch targets and help.
4. Import the invented ten-row example, scroll with the keyboard open, and reach
   Use sample/Cancel. Rotate the phone and confirm Apply/Discard remain reachable.

Record device/browser and observations before accepting this UI. Existing
clinical-policy, native/offline installation and binary-redistribution gates
remain open. No Windows candidate was rebuilt by this change.
