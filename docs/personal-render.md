# Personal Render test

This is a personal weekend test, with invented data and session-only state.
It does not change the release's supported platforms or accept the pending PRs.
Status and the required next action live in `progress.json`.

Actual local captures: [narrow Properties and actions](images/render-mobile-light-properties.png)
and [import footer at reduced height](images/render-mobile-dark-import.png).

## Source and service

Deployment branch: `deploy/render-personal-weekend`.
Base commit: `db6571c1f69b60eef34cefcadf4c89f1e29ad042` (draft PR24).
The newer saved E60 P1/P2 recovery changes are included, with original input
hashes retained at `outputs/render-personal/recovery-input-hashes.json`.
The original recovery worktree and existing review snapshots remain unchanged.
Until publication, this is explicitly a dirty source snapshot, not a new commit.

`render.yaml` prepares a single Free Python web service in Frankfurt. Use the
repository root, deployment branch and manual deployment (`autoDeployTrigger:
off`). The existing `.python-version` and explicit service `PYTHON_VERSION`
select standard Python3.14.8; the existing `requirements-ui.lock` is reused.
All48 pins resolve to Linux x86_64/Python3.14 wheels in a pip dry-run; actual
Linux dependency installation and the Render build still need execution.

- Build: `python -m pip install -r requirements-ui.lock && python -m pip check`
- Start: `python -m ravel.web`
- Health check: `/healthz`
- Host: `0.0.0.0`; port: `PORT` (fallback10000); reload disabled.
- Secrets, supplied in Render's Environment panel only:
  `RAVEL_AUTH_USERNAME` (nonempty, no colon), `RAVEL_AUTH_PASSWORD` (at least
  16 characters; use a unique random value).

Missing secrets or an invalid port stop startup. The Blueprint prompts for
secret values with `sync: false`; it contains no credential. Neither an `.env`
file nor browser JavaScript stores the hosting password. Connect the Render
plugin/account and authorize the Ravel Git repository before creation if needed.
After the permitted commit/push, deploy that exact commit and record the actual
Render service URL and deploy commit; do not infer a URL from the service name.
Keep PRs unmerged. Do not upgrade the service plan.

The ordinary `python -m ravel ui` remains at `127.0.0.1:8090`, and `--port`
still works without authentication or hosting secrets. Do not expose that local
entry point as the hosted service.

## Access and session behavior

HTTP Basic authentication covers pages, assets, upload endpoints, polling and
WebSocket handshakes. GET/HEAD `/healthz` returns only `ok`, without application
state. Requests with a foreign Origin are refused; WebSockets also require a
same-host Origin. Use Render HTTPS; credentials rely on its TLS termination.
Recipe/CSV bytes are sent to the page's Socket.IO client and downloaded as
browser-local blobs. File-route downloads, if added later, pass through the same
HTTP gate. Private page responses are marked `no-store`; public framework assets
can retain NiceGUI's static cache settings.

The password is a shared personal entry gate, not a multi-user authorization
system. Each page creates its own Workspace; separate contexts must retain their
own columns, rows and generated results. There is no cross-user permission model.
Browser Basic credentials may remain cached until the browser/profile closes;
there is no application logout. An incognito browser is convenient for the test.

Save recipes and CSV before closing/reloading or a restart. Render Free can
[sleep after15 idle minutes, restart, and lose local files](https://render.com/docs/free).
Cold start can take about a minute. No database/disk, background keepalive or
production-availability promise is added. The full engine limits are unchanged;
large jobs near them may exceed the Free instance's resources. The requested
1,000-row workflow is the hosting test target.

## Verification and Pixel try-out

With the source and review environments from `development.md`:

```powershell
python -m unittest discover -s tests -v
python scripts/check_personal_web.py --output outputs/render-personal/new-local-run
python scripts/build_dashboard.py --check
git diff --check
```

The browser command requires the existing Playwright review dependencies and
installed Chrome. Its default starts and stops its own protected server, with
random ephemeral test credentials only in child-process memory. It never writes
credentials into evidence. A fresh output directory preserves previous failures.
For the deployed service, run the same checker with
`--base-url https://ACTUAL-SERVICE.onrender.com` and the two secrets supplied to
the checking process from the hosting secret manager. Do not paste secrets into
commands, documentation, screenshots or chat. That remote run is still required.

Run `python scripts/check_personal_web.py --desktop --output
outputs/render-personal/new-desktop-run` for the maintained full matrix on an
owned, source-attested loopback server. Never automate the frozen manual-review
instances. Local mobile emulation uses412x915 portrait,
915x412 landscape and412x420 reduced height in both themes, including separately
scrollable definitions, import actions, Properties and Apply/Discard. Reduced
height is only an approximation of the Android visual keyboard viewport.

Required on the actual hosted Pixel8: authenticate over HTTPS, create/generate
1,000 rows, change Maximum to20/Apply, change to30/Discard and expect20, regenerate,
download CSV/recipe, import the invented `examples/sample-assisted/ten-rows.csv`,
confirm the displayed identifier rules and generate1,000 rows. Expect first
generated sample ID11 and last1010, with `generated` row origin. Rotate both ways,
focus/edit a field with Gboard open and reach Properties/Apply/Discard by scrolling.
Repeat in an independent incognito session: its table settings/result must not
change when the first session changes. Record actual results, deployment commit,
browser/Android versions and any viewport/keyboard obstruction before acceptance.
