# Sample-assisted single-table workflow — version-2 contract

Contract for [issue #12](https://github.com/Maks1m-Se/ravel/issues/12), established
before implementation while generator PR #10 is under joint code review.
Invented reference data does not establish milestone acceptance. Preserve the
accepted Fichte appearance, comfortable Properties interaction and completed
explicit-rule engine. No clinical rules, linked tables or packaging work are
introduced here.

The later [version3 rules](extended-rules.md) add finite-domain uniqueness and
exact quotas to this same source-bound flow; version2 semantics remain unchanged.

## User flow

1. **Start from a sample** selects a local UTF-8 CSV. Parse logical CSV records,
   including quoted commas/newlines, without changing or overwriting the file.
   Show a source preview and editable suggested types, missingness, numeric
   ranges and categories. Keep unsupported or ambiguous input explicit.
2. Mark each applied assumption **Sample**, **Edited** or **Explicit**. Drafts
   remain distinct from applied assumptions. Ten rows describe this sample;
   observed ranges and category frequencies do not establish population bounds
   or associations. Independent marginal generation does not preserve correlation.
3. Exclude identifier fields from fitting by default. For the reference below,
   explicitly confirm `sample_id` as a positive integer identifier and choose
   sequential generated IDs starting at 11. Do not fit or resample those IDs.
4. Select **Generate new rows** or **Extend to total**. Show retained + generated
   = output counts before generation, then use the existing Apply, Generate,
   actual Preview, CSV, recipe and run-record flow. Changing a source, assumption,
   mode or count makes old results stale and blocks export until regeneration.
5. Save/reload a source-aware recipe and repeat with the same environment. Invalid
   input or failed validation preserves the current source, applied assumptions,
   drafts, selection and result. No automatic overwrite, migration or hidden edits.

The compact start screen and existing workspace remain. Add only the source,
assumption-origin and output-mode controls needed for this flow. Preserve focus,
readable errors, keyboard access, themes, Fields/Preview and width preference.

## Hand-worked ten-row reference

[ten-rows.csv](../examples/sample-assisted/ten-rows.csv) is invented. Its exact
source cells, descriptive expectations and checksum are recorded separately in
[ten-rows.expected.json](../examples/sample-assisted/ten-rows.expected.json).

| Field | Observed reference | Proposed editable assumption |
| --- | --- | --- |
| `sample_id` | Integers 1–10, unique and nonmissing | Identifier excluded from fitting; explicit sequential rule starts at 11 |
| `length_mm` | 8 observed, 2 empty; min 9.8, max 12.2; sum 87.0, mean 10.875 | Decimal uniform ticks 9.8–12.2 at one decimal place; independent missing probability 0.2 |
| `material` | A: 6; B: 4; no empty cells | Categories A/B with probabilities 0.6/0.4, missing probability 0 |

Uniform ticks are a visible starting assumption, not an inferred distribution.
The descriptive mean is not a fitted generator parameter. Missingness and
categories remain probabilities, not exact quotas. Users may explicitly change
the bounds, missingness and categories, including declaring a new category.

| Requested mode/count | Retained | Generated | Output | IDs | Row origin |
| --- | ---: | ---: | ---: | --- | --- |
| Generate 1,000 new | 0 | 1,000 | 1,000 | 11–1,010 | All `generated` |
| Extend to 1,000 total | 10 | 990 | 1,000 | Retained 1–10; generated 11–1,000 | First 10 `retained`; then 990 `generated` |
| Extend to 10 total | 10 | 0 | 10 | Original 1–10 | All `retained`; do not invoke an engine request for zero rows |
| Extend to 9 total | — | — | Rejected | No partial result | Original state and files unchanged |

Retained records keep their order and exact decoded cell text: `10.0` stays
`10.0`, and the two empty cells stay empty. Appending metadata or quoting CSV
does not imply byte-identical output files; the input file's bytes stay intact.
Append the reserved export column `row_origin` with `retained` or `generated`.
Reject a conflicting source header clearly rather than silently renaming it.
An output sidecar records source checksum, applied recipe and environment.

## Deterministic override reference

Before implementation, fix a second tiny result by hand. Override length to the
singleton 12.2 at one decimal place with zero missingness; explicitly declare
material C with probability 1 and zero missingness; keep generated IDs from 11.
Seed 17 is recorded, although these rules do not require random expectations.

- [generated-two.expected.csv](../examples/sample-assisted/generated-two.expected.csv)
  contains exactly `(11, 12.2, C, generated)` and `(12, 12.2, C, generated)`.
- [extend-twelve.expected.csv](../examples/sample-assisted/extend-twelve.expected.csv)
  contains the ten unchanged source records marked retained, then those two rows.

These files are expected results, not output claimed from a sample application.
They check explicit overrides, a newly declared category, counts, original
preservation and origin independently of the implementation.

## Recipe and validation

Use source-aware `ravel-single-table/2`; a version-1 recipe remains version 1. Keep
version-1 reading and its explicit-rule output semantics unchanged; do not
silently migrate saved recipes. Reuse the shared field validator, generation
streams and serializers. Sample profiling and retain/append composition belong
in adapters outside the generic random rules and outside the UI.

A source-aware saved recipe embeds the original UTF-8 CSV text, its byte checksum,
the applied rules, stable identities, source-versus-user assumption provenance,
mode, target count and seed. No external path or original file is needed to
reload offline. Preserve any BOM/line-ending bytes in the embedded text; strip a
BOM only when interpreting the first header. Validate the complete canonical
UTF-8 saved recipe, including embedded source, against the 1 MiB bound before
replacing state. A valid compact import must not become an unsaveable recipe.

Version 2 also supports `text_id` with an explicit text prefix, positive integer
start and minimum digit width (1–20). Padding preserves leading zeroes without
coercing retained source cells. Generated IDs are checked for collisions against
source identifiers; unsupported source identifier schemes require a deliberate
supported rule. Suggested identifier rules require explicit confirmation before
new rows can be generated. Duplicate or empty retained identifiers fail clearly
when used as identifiers. Source-binding checksum mismatches are errors.

Only exactly empty cells count as missing. Delimiters are explicitly comma,
semicolon or tab; UTF-8 with or without BOM is supported. Category suggestions
use observed frequencies rounded to a 12-place integer grid with remainders
allocated in stable source order so probabilities sum exactly to one. Numeric
suggestions use the existing bounded integer/decimal rules; ambiguous numeric
text such as leading-zero codes stays text. Source assumptions and later edits
are stored separately, and identifier fitting is excluded.

Use the current supported scalar bounds and decimal grid. Keep output within
100,000 rows, 50 columns including row origin, and two million cells. Reject
empty/duplicate/invalid headers, inconsistent logical row widths, undecodable
UTF-8, empty samples, unsupported numeric values and reserved-origin collisions
with actionable errors. Do not trim or coerce retained cells. Only exactly empty
cells represent sample missingness in this bounded proposal; expose ambiguity
instead of treating arbitrary text such as `NA` as missing.

## Verification reference

- Independently check the ten-row profile above, identifier exclusion and
  assumption provenance before connecting generation.
- Check exact counts/origin/retained lexemes for both 1,000-row modes, the zero-new
  boundary and rejected target below source count. Generated rows obey the
  approved types, grid, bounds and categories; do not require probabilistic counts
  to be exact. For 1,000 draws, broad six-SD reference intervals are 124–276
  missing lengths and 507–693 material-A values; these are test tolerances.
- Compare the two tiny deterministic outputs to the hand-worked files. Preserve
  source bytes and retained values through save/reload and UI/CLI execution.
- Test invalid/ambiguous CSV, quoted text/newlines/Unicode, failed edits/imports,
  serialized size boundaries, stale exports and clear recovery without data loss.
- Run browser checks in both themes/laptop sizes, with real preview/CSV and
  original Properties/viewport/focus/draft regressions. Get maintainer feedback
  on comfortable source review, assumptions and count controls.

## Try the local implementation

On the start screen choose **Start from sample**, use comma as the delimiter and
select `examples/sample-assisted/ten-rows.csv`. Review the displayed assumptions
and explicitly check the sequential identifier policy before **Use sample**.
Generate 1,000 new rows, then choose **Extend to total**, Apply and Generate.
The count strip reads 10 retained + 990 new = 1,000 output. Source shows the
original ten rows; Preview shows actual output and CSV uses the same formatter.
Edit the length range or categories in Properties, Apply, then regenerate. A
changed identifier policy needs confirmation again. Save/reload the recipe;
its embedded source permits repeating the run without locating the input file.

The CLI uses that same core (run with the documented source interpreter):

```bash
python -m ravel sample examples/sample-assisted/ten-rows.csv --recipe sample.recipe.json --mode extend --rows 1000 --confirm-identifiers
python -m ravel validate sample.recipe.json
python -m ravel generate sample.recipe.json --csv sample.csv
```

Choose unused output names: files are never overwritten. Without
`--confirm-identifiers`, profiling still saves editable assumptions but
generation requires confirmation of an appropriate identifier rule.

The authorized implementation remains subject to joint review. Actual checks
and limitations are recorded in progress.json, not inferred from this reference.
M0/full M1 and native/platform/clean-machine/license/distribution/release gates
remain open; NiceGUI remains provisional. Work was AI-assisted; the invented
fixtures do not establish clinical validation.
