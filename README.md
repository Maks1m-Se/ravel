<picture>
  <source media="(prefers-color-scheme: dark)" srcset="brand/lockup/ravel-lockup-dark.svg">
  <source media="(prefers-color-scheme: light)" srcset="brand/lockup/ravel-lockup-light.svg">
  <img src="brand/lockup/ravel-lockup-light.svg" alt="Ravel" width="225" height="64">
</picture>

Ravel composes reproducible synthetic test data from explicit rules or an invented
CSV sample. The current preview supports editable sample assumptions, new-row or
retain-and-extend generation, and small linked datasets. It is available for
review and is not a supported application release.

**Compose the data you need.**

![Ravel linked workbench with an actual measurement preview in Dark](docs/images/linked-generated-dark.png)

## Build a table

Add, duplicate, rename, configure and remove columns. Choose sequential IDs,
constant text, numeric sequences, bounded random integers/decimals or categorical
values with explicit probabilities. Additional rules include normal values,
Booleans, dates/day sequences, finite-domain uniqueness and exact category quotas.
Set row count, seed and per-cell missingness,
then **Apply changes → Generate table**. Preview shows the first 100 actual rows;
**Export CSV**, **Save recipe** and **Save run record** retain the data, exact rules,
generating environment and checksums.

Unapplied or invalid edits cannot be silently ignored. Changed settings mark the
previous result **Out of date** and block CSV export until a current result is
generated. Column removal asks for confirmation. Drafts and errors survive theme,
view and layout changes. Drag the Properties divider or focus it and use arrows;
**Reset layout** restores its default preference, including after window resizing.

Choose **Start from sample** to import an invented UTF-8 CSV. Review/edit ranges,
categories and missingness, and explicitly confirm identifier generation. Generate
1,000 new rows, or extend ten originals to1,000 total with their exact cell text
and order retained. `row_origin` distinguishes retained and generated rows; the
saved recipe embeds the checked source for reproducible reload.

Choose **Use template** for Devices / measurements: three devices, two child
measurements per device. Select tables, review parent/key/count changes and
generate one current dataset. **Export dataset ZIP** includes every table CSV,
recipe, dictionary and validation/run information. CLI `--directory` stages the
same files into a fresh destination. See the [sample](docs/sample-assisted.md),
[extended-rule](docs/extended-rules.md) and [linked-table](docs/linked-tables.md)
contracts and their hand-worked fixtures.

The headless engine and CLI use the same versioned recipe, validation and CSV
serializer as the UI. Stable field identities and separate random streams mean
adding an independent column preserves existing generated columns. Duplicated
columns get new identities. Reproducibility is scoped to the recorded environment.

### Source quickstart

Use standard **CPython 3.14.8 x64**, with the GIL enabled, on Windows. In PowerShell
at the repository root, create a separate source environment:

```powershell
py -3.14 -m venv .venv-source
.\.venv-source\Scripts\python.exe --version
.\.venv-source\Scripts\python.exe -m pip install -r requirements-ui.lock
.\.venv-source\Scripts\python.exe -m pip check
.\.venv-source\Scripts\python.exe -m ravel ui
```

Verify that the version command reports **3.14.8**. Open
**http://127.0.0.1:8090/** and choose **Create table**. Stop with Ctrl+C.
Installation needs network access; the app serves assets locally. Save before
closing the page: state is session-only. NiceGUI remains provisional.

### Headless example

The core and CLI need only the standard library. With the same interpreter:

```powershell
New-Item -ItemType Directory -Force outputs/tryout
.\.venv-source\Scripts\python.exe -m ravel validate examples/three-rows.recipe.json
.\.venv-source\Scripts\python.exe -m ravel generate examples/three-rows.recipe.json --csv outputs/tryout/reference.csv
```

Expected rows: `(1, demo, 10)`, `(2, demo, 12)`, `(3, demo, 14)`. The CLI writes
CSV, canonical `.recipe.json` and `.run.json` sidecars and refuses to overwrite
existing files. Choose a fresh output filename for another run.

The [single-table contract](docs/single-table.md) defines bounds, decimal scale,
probability semantics, CSV and limits. The app explicitly rejects the old
workbook experiment JSON; it never silently migrates or overwrites the original.
Arbitrary joins, joined-sample fitting and clinical derivations remain outside
this generic increment. The [clinical preparation](docs/clinical-template-preparation.md)
requires numeric-policy review before clinical implementation. A
[private Windows preview build/checklist](docs/windows-preview.md) is available
for development review; clean-machine, native/offline and artifact-specific
redistribution checks remain open. M0/full M1 and release gates are incomplete.
The [candidate verification record](docs/windows-preview-validation.md) identifies
the exact private artifact, actual checks, review PRs and joint function test.

See the [development guide](docs/development.md#single-table-source-development)
for maintained checks and a short walkthrough. Historical
[fixture experiment instructions](docs/development.md#workbook-experiment) and
packaging evidence remain available, with their original scope.

A password-protected [personal Render test](docs/personal-render.md) is prepared
on a separate deployment branch, with a narrow-screen layout. Hosted verification
and actual Pixel8 keyboard review remain separate from the desktop source checks.

## Documentation and contributing

- [Product plan](docs/plan.md) and [recipe architecture](docs/specification.md)
- [Clinical reference cases](docs/baseline-specification.md): an optional domain
  template, with invented specification examples rather than generated results
- [Environment proposals and decisions](docs/decisions.md)
- [Contributor guide](CONTRIBUTING.md) and
  [prototype dependency/license inventory](docs/dependency-licenses.md)

Development, including code and documentation, is AI-assisted. The maintainer
reviews and accepts changes; AI assistance does not establish clinical correctness.

Licensed under the [MIT License](LICENSE). Copyright 2026 Maksim Sendetski.
