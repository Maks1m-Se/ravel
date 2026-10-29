# Main integration candidate — 29 October 2026

This is a reviewed integration snapshot, not a second progress tracker.
[progress.json](progress.json) remains authoritative. AI-assisted preparation and
verification do not replace maintainer acceptance.

## Candidate and preserved state

- Branch: `integration/main-2026-10-29`, isolated at
  `C:/Git/ravel/outputs/integration-2026-10-29/worktree`.
- Starting `origin/main`: `d7d42f8bd183fd4bb3e7b9005ac7324b7a3d0b90`.
- All nine heads below were checked as ancestors and fast-forwarded in order
  on this local candidate. There were no conflicts or synthetic merge fixes.
  Their combined tree is PR25 head
  `7c6042e532aef523cbd5f32700184e80649ee142`.
- Follow-up changes here only update documentation/progress/dashboard. Runtime,
  scripts, tests, examples and locks retain the checked PR25 bytes.
- Existing main/feature/deployment worktrees are preserved. Inventories include
  HEAD, porcelain status and SHA256 of modified/untracked files: 17 files in the
  older recovery worktree and 76 in the staged worktree. Neither was used as an
  implicit extra input. Raw inventory: ignored
  `outputs/integration-2026-10-29/original-worktrees.json`.
- No actual PR merge, retarget, readiness change or Render deployment is part of
  this preparation. The existing Free demo continues to run
  `79e44cb405033aa16e8459c59903c3120643656d` at
  [the HTTPS URL](https://ravel-personal-test.onrender.com/).
  This candidate's runtime is identical to that deployment.

## Exact PR order after approval

GitHub readback found exactly nine open PRs, all draft, all individually
mergeable. All PR conversation/review timelines and review threads were empty.
Each head contains its predecessor's complete head; there are no sibling feature
branches to combine.

| Order | PR | Head branch | Checked head SHA | Current base |
| --- | --- | --- | --- | --- |
| 1 | [#10](https://github.com/Maks1m-Se/ravel/pull/10) | `feature/single-table-generator` | `d9bcec2a752c382b17e8e90d40a7986e8bb2639f` | `main` |
| 2 | [#18](https://github.com/Maks1m-Se/ravel/pull/18) | `feature/sample-assisted` | `b6fae41a4ef72b22d2bbe9d48a97fa4f5d6d25bd` | `feature/single-table-generator` |
| 3 | [#19](https://github.com/Maks1m-Se/ravel/pull/19) | `feature/generator-ux` | `9e86648bde08f38d7cffd77f17f2fad251d8bd52` | `feature/sample-assisted` |
| 4 | [#20](https://github.com/Maks1m-Se/ravel/pull/20) | `feature/extended-rules` | `d0aec989c5f756b8b7c6c3f021784d1625348cd8` | `feature/generator-ux` |
| 5 | [#21](https://github.com/Maks1m-Se/ravel/pull/21) | `feature/linked-tables` | `6a50e5fa6c89683aade934260378434cd81b71d3` | `feature/extended-rules` |
| 6 | [#22](https://github.com/Maks1m-Se/ravel/pull/22) | `docs/clinical-template-preparation` | `f96a1def5c7b0a7412c6cd7faeb98a7f8b88dca8` | `feature/linked-tables` |
| 7 | [#23](https://github.com/Maks1m-Se/ravel/pull/23) | `feature/windows-preview` | `2c235bb34512c6d76ee4bc143cbf0ddba5e6970c` | `docs/clinical-template-preparation` |
| 8 | [#24](https://github.com/Maks1m-Se/ravel/pull/24) | `fix/pending-edit-actions` | `db6571c1f69b60eef34cefcadf4c89f1e29ad042` | `feature/windows-preview` |
| 9 | [#25](https://github.com/Maks1m-Se/ravel/pull/25) | `deploy/render-personal-weekend` | `7c6042e532aef523cbd5f32700184e80649ee142` | `fix/pending-edit-actions` |

Use merge commits (or an explicitly approved history-preserving fast-forward
process), keeping these ancestors intact. Squashing/rebasing each stacked PR
would discard the proven dependency graph and requires a new integration check.

After approving the candidate and desktop walkthrough:

1. Re-read all nine remote heads and `main`; stop and reassess if they differ
   from this snapshot. Complete each PR's maintainer review/readiness decision.
2. Merge #10 into `main`.
3. Retarget #18 to `main`, confirm its diff contains only the next increment,
   then merge it. Repeat for #19, #20, #21, #22, #23, #24 and #25 in that order.
   Keep feature branches until the whole stack is integrated.
4. Integrate this branch's documentation-only follow-up last, through the
   maintainer-approved PR/process. The resulting main tree should equal this
   candidate (merge-node SHAs will naturally differ). Recheck dashboard and core
   CI on the actual main result.

No merge command has been executed against `main` or GitHub. The nine draft PRs
remain available for review. The candidate branch is a review artifact, not an
alternative authorization to merge the whole stack at once.

## Remaining review findings and scope

| Finding | Disposition in this candidate |
| --- | --- |
| Canonical saved recipe exceeded 1 MiB / failed load mutated state (#10) | Repaired in d9bcec2; saved-size and atomic-state regressions retained. |
| Zero-new extension identifier checks and exact-quota provenance (#18/#20) | Repaired in d0aec98; core/sample/extended coverage retained. |
| Stale Session help and enabled Apply without drafts (supplied Claude F1/F2, issue #13) | Repaired in the #24 stack; pending/no-draft/exact-revert/stale-output checks retained. |
| Short-height Apply/Discard and import footer friction (issue #13 addendum) | Stable action areas implemented in #24; pointer/keyboard and short-height browser checks retained. |
| P1 action focus and P2 obsolete validation messages | Saved E60 corrections published in d58e977, inherited by #25; recovery workflow checks them. The original dirty worktree remains untouched. |
| Public recipe embedded-source bypass and omitted row_origin cells | Repaired in 79e44cb; two red-before-green units and deployed boundary/recovery coverage recorded in E65–E67. |
| Intermittent menu post-theme focus assertion | Not reproduced by the final prior complete runs; no speculative fix or confirmed correctness blocker. Retain earlier failed evidence. |
| Windows Proactor connection-reset diagnostics after socket rejection | Prior local logs retained; no repair or blanket clean-log claim. This is separate from browser page errors and HTTPS evidence. |

No unresolved GitHub review thread exists in this snapshot. Passing tests are
not a guarantee that undiscovered defects are absent. The remaining source
integration approval is **maintainer desktop acceptance and explicit merge
authorization**. No known uncorrected technical defect currently blocks this
bounded source integration, subject to the verification record below.

The following retain their real scope:

- **Actual Pixel 8/Gboard: deferred by the maintainer; not performed, not passed.**
  It is no longer a prerequisite for this source integration. Portrait/landscape/
  reduced-height emulation remains automated evidence only; no phone or mobile
  support acceptance is implied.
- Desktop subjective visual/function acceptance remains unperformed for this
  exact integrated candidate. E46 acceptance belongs to its earlier sources.
- Clinical numeric policy/reference transcription needs maintainer review before
  future clinical derivations. #22 merges preparation proposals only; no clinical
  arithmetic or Python/R validation is adopted by integrating these files.
- Clean-machine/native/offline/platform tests and artifact-specific transformed
  frontend/font/native/vendor/Microsoft-runtime findings block the relevant
  distribution/release claims. They do not block merging source/build tooling.
  No current Windows binary was rebuilt or publicly released.
- M0/full M1, NiceGUI adoption and R1–R10 release gates stay unchanged.

## Automated verification

Candidate-specific results and fresh-checkout commands are recorded in E68 and
the final verification section below. Raw logs, captures, inventory and lock
installation reports stay in ignored `outputs/integration-2026-10-29/`.
Earlier passing evidence is reused only for unchanged bytes and original scope;
failed runs remain separate.

For a new PowerShell checkout, use the README source quickstart. With the selected
standard CPython 3.14.8 and UI/review lock dependencies:

```powershell
python -m unittest discover -s tests -v
python scripts/build_dashboard.py --check
python scripts/check_clinical_review.py
python -m pip check
python scripts/check_personal_web.py --desktop --output outputs/integration-desktop-new
python scripts/check_public_demo.py --output outputs/integration-public-new
git diff --check
```

Browser commands own and stop their dedicated servers. They do not operate any
older frozen manual-review instance. Use fresh output directories.

## Short required desktop acceptance

Use [the existing demo](https://ravel-personal-test.onrender.com/) or launch this
candidate with `python -m ravel ui --port 8090`. The demo has the same runtime,
with smaller public workload limits. Use invented data only. At 1366×657 and
1280×800 in both Light/Dark:

1. Create a table; Generate should report 1,000 rows with the first 100 previewed.
   Download CSV, recipe and run record. Expect IDs 1–1000 and readable controls.
2. Select value, set Maximum20, switch theme, then Apply. Generate again.
   Change Maximum30 and Discard: expect20 and current export. Try Minimum200/
   Maximum20: Apply must focus the error; editing a participating bound clears
   its historical error without applying the draft. Correct and Apply.
3. Tab through More options, named Add/Duplicate/Remove (cancel once), Properties,
   Apply/Discard. Resize Properties and switch Fields/Preview; drafts and
   keyboard focus should remain clear. The actions must stay visible at short
   height without hiding the scrolling form's final input.
4. Import `examples/sample-assisted/ten-rows.csv`; inspect originals and
   assumptions, confirm identifiers, reach Use sample/Cancel in the stable
   footer. Generate1,000 new rows, then try extension to1,000 total: ten original
   rows first,990 generated and explicit row_origin.
5. Home > Use template > Devices / measurements. Expect three devices and six
   child measurements. Switch tables by keyboard and download the complete ZIP.

Record OS/browser, exact candidate/runtime identity, observations and an explicit
desktop accept/reject decision in the existing progress record. Do not report the
deferred phone/keyboard check as completed.


## Executed verification — 29 October

Windows source environment: standard CPython3.14.8 x64/GIL, NiceGUI3.18.0,
Playwright1.58.0, Chrome156.0.8078.73. Runtime fingerprint:
`a5b75e9951f4ab5cdf2a11e0c56402a2637ca03835273d93f4799179c8eace19`.

| Check | Actual result / scope |
| --- | --- |
| Core suite | 96 unit tests pass on the integrated runtime. |
| Full desktop browser matrix | 24 cases pass: rules/sample/extended/linked/pending/recovery, Light/Dark,1366×657/1280×800; zero page errors/external HTTP/WebSockets. |
| Local public demo | Five cases pass: compact controls, both mobile themes/orientations/reduced height, transport limits, source/cell boundary recovery and separate sessions. Zero page errors. |
| Fresh checkout and environment | Independent `git clone --no-local`, no borrowed PYTHONPATH; new venv installs48 runtime + four review pins. Pip/52 exact versions,96 units, dashboard and clinical structural checker pass. |
| Fresh CLI | Hand rows `(1,demo,10)`, `(2,demo,12)`, `(3,demo,14)`; no-overwrite and1,000 sample rows with IDs11–1010/generated origins pass. |
| Fresh checkout browser | Four additional recovery cases pass in both themes/sizes, with zero page errors/external browser requests. |
| Protected hosting regression | Two additional fresh-checkout cases pass with anonymous/wrong credentials rejected, authenticated uploads/downloads/WebSockets and independent contexts. Ephemeral invented credentials stay in test-process memory. |
| Fixed statistical subset | All five previously specified seeds at n100000 pass the unchanged normal/Bernoulli thresholds. No Gaussian-pair or completeR5 claim. |
| Current demo readback | Existing Render service remains Free/Frankfurt/manual; deployment79e44cb is live; fresh TLS-validated `/healthz` returns200/ok. Prior full HTTPS five-case evidence is E67, not recounted as today's browser run. |

The fresh runtime clone begins at7c6042e, containing the same runtime/scripts/
tests/locks as the candidate. Final documentation/tracking checks are repeated
after preparing the records. Raw final logs live under the directory listed
above. The original worktree preservation inventory is verified again.

Two ad-hoc fresh CLI attempts failed because the harness expected exit1 instead
of the documented2, then chose an output whose sidecar collided with the recipe.
Both were correct application refusals; corrected commands pass, no product
repair is claimed. Failed artifacts/logs are retained. The existing browser
helper emits a Python invalid-escape SyntaxWarning for its JS regex on first
import; checks complete and this is not a runtime-app failure. No source edits
or speculative focus/connection-reset fixes were introduced.

Actual new captures: [Light pending actions](images/integration-desktop-pending-light.png)
and [Dark short-height import footer](images/integration-desktop-import-dark.png).
They were inspected and copied without alteration. Fresh recovery/linked
captures at1280×800 were also inspected. Human desktop acceptance remains
separate; actual Pixel/Gboard is **deferred, not performed, not passed**.
