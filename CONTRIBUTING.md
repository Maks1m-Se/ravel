# Contributing to Ravel

Ravel is an early prototype. Read [AGENTS.md](AGENTS.md), the
[plan](docs/plan.md) and [current progress](docs/progress.json) before work.
The bounded explicit-rule single-table generator is implemented; sample and
clinical generation remain planned. NiceGUI and distribution choices
remain provisional. Discuss clinical rules, recipe changes, dependency/license
changes and important interface behavior with the maintainer before acceptance.

Use the [single-table source setup](docs/development.md#single-table-source-development).
Historical experiment instructions remain in the
[Windows workbook setup](docs/development.md#workbook-experiment),
[verified fresh-checkout commands](docs/development.md#fresh-checkout-smoke) and
[isolated packaging recipe](docs/development.md#windows-folder-bundle-experiment).
These are same-host Windows instructions, not tested cross-platform setup.
The [dashboard checks](docs/development.md#view-and-check-the-dashboard) use
Python 3.11+ and the standard library. Run relevant unit/documentation checks;
for interface changes also run the maintained browser check described in the
workbook guide. Report actual commands/results, failures and checks not run.
Keep environments, wheels, bundles and review output under ignored `outputs/`.

Use a focused branch and small PR. Explain the concrete problem, resulting
behavior, meaningful checks and material limitations. Update affected docs and
progress evidence; regenerate the dashboard after changing its inputs. Preserve
historical evidence. Include screenshots for appearance changes and reproducible
invented examples for bugs. Independently establish expected clinical/statistical
results before implementing derivations; the maintainer reviews consequential
rules and accepts results. A passing check alone does not establish a release gate.

Use only invented data in examples, tests, screenshots and bug reports. Never
commit confidential samples, credentials or sensitive configuration. Keep generic
generation, clinical rules and interface code separate. New dependencies require
versions, source/license references and redistribution notices; consult the
[prototype inventory](docs/dependency-licenses.md), whose gaps remain open.

AI assistance is welcome and must be disclosed in the PR with its scope. The
contributor remains responsible for understanding and reviewing submitted code,
data provenance, licenses and test evidence, including AI-generated content.
Do not claim independent clinical validation from AI review. Contributions to
Ravel use the repository's [MIT license](LICENSE); third-party terms remain theirs.

Release changes follow the [plan's release/update policy](docs/plan.md): tested
commits, immutable versioned artifacts, checksums/notices, honest limitations and
manual offline-capable updates. The maintainer owns merge and release decisions.
