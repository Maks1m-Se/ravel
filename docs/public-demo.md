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

The previous protected deployment is `d58e977ab2cac654c5012918e35b26fc899ab0f4`,
deploy `dep-dbdhvit9fdbs73b6rnv0`. Record the new deployment and hosted checks
below after they actually complete. Do not infer hosted behavior from localhost.

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
