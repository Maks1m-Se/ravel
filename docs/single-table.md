# Explicit-rule single-table increment

This contract was established before implementation on 15 October 2026. It is a
bounded M1-01/M1-02 increment, not completion of M0 or M1. Sample profiling and
retain-and-extend follow next, then linked tables; both generic entry paths
remain required for the first usable release. Clinical derivations and binaries
are outside this batch. Several sequential implementation stages precede joint
maintainer review under the approved sequencing exception.

This document specifies version1. The implemented [sample path](sample-assisted.md)
uses version2; [bounded extended rules](extended-rules.md) use version3. These
additions preserve version1 behavior and do not silently migrate saved files.

## Recipe version 1

JSON format `ravel-single-table/1` contains `seed`, one `table` with stable `id`,
`name`, `row_count`, and an ordered nonempty `fields` list. Every field has a
stable `id`, display/CSV `name`, `kind`, `missing_probability`, and rule parameters.
IDs are independent of names and order, preserved by save/reload, and newly
allocated on duplication. Unknown keys, versions and rules fail clearly. JSON
duplicate keys, nonfinite values and booleans masquerading as numbers fail.
The experiment's `ravel-workbook-experiment/1` is rejected explicitly; no silent
migration or overwrite occurs. The old experiment remains available separately.

| Rule | Parameters and semantics |
| --- | --- |
| `id` | Positive integer `start`; increases by one per row, unique/nonmissing |
| `constant` | Nonempty text `value`; literal text, including commas/newlines, no expression evaluation |
| `sequence` | Integer `start`, integer `step` (including zero/negative); row i is start + i × step |
| `integer` | Integer `minimum` and `maximum`; uniform over both inclusive endpoints |
| `decimal` | Decimal-string `minimum`/`maximum` and integer `places` 0–6; bounds must lie on that grid; uniform over inclusive integer ticks, exported at exactly that scale |
| `category` | Nonempty distinct text `values` and decimal-string `probabilities`; nonnegative, at least one positive, sum exactly one; independent weighted draws, zero-weight values never drawn |

Counts: 1–100,000 rows, 1–50 fields, at most 2,000,000 cells. Integer/sequence
endpoints and decimal bounds are within ±1,000,000,000,000; IDs remain positive
and within that limit. Names are unique, trimmed, nonempty, at most 40 characters;
stable IDs match `[A-Za-z][A-Za-z0-9_-]{0,63}`. Text values are nonempty and at most
200 characters; categories number at most 100. Seed is an integer 0–2^63−1.
Uploaded and canonically saved UTF-8 recipes must both fit within 1 MiB.
Validation checks the saved representation before applying or loading rules,
so a compact upload cannot expand into a saved recipe that cannot be reloaded.
These are explicit increment limits, not release benchmarks.

`missing_probability` is a decimal string between 0 and 1. Independent Bernoulli
draws decide whether each cell is missing; counts are not exact quotas. ID fields
must have zero missingness. Category probabilities apply conditional on a cell
being present. Exact quotas, dependencies and uniqueness outside IDs are
unsupported, and unknown requests fail rather than silently relaxing them.

Each field has separate value and missingness streams derived with SHA-256 from
the seed, table identity, field identity and stream purpose. Streams use Python's
`random.Random`. Names/order/other fields do not participate. Adding or renaming
an independent field preserves existing generated columns; changing missingness
does not shift the present values' underlying row draws. Duplicates have their
own streams. Reproducibility is promised within the recorded pinned environment,
not across arbitrary Python versions or later generator revisions.

## Result and adapters

The engine validates the complete recipe before generation and returns an
immutable result with its canonical recipe, ordered headers, typed rows and
environment metadata. It does not read UI state. The CLI and UI call this same
validation, generator and CSV serializer. Invalid requests produce no successful
partial result. Decimal cells use `Decimal`, integer/ID/sequence cells use `int`,
text/category cells use `str`, and missing cells use `None`.

CSV is UTF-8 without BOM, LF line endings, one header row in field order, no index,
decimal integers, fixed-scale non-exponent decimal text, and empty cells for
missingness. All CSV cells and headers are quoted, including integers and empty
cells, so literal carriage returns, line feeds, commas and quotes round-trip.
Nonempty text avoids conflating empty string and missing values. Text is literal, including formula-
looking strings; spreadsheet software may interpret them when opening CSV.
Preview uses the same cell serializer as CSV and shows the first 100 rows of the
actual result. A changed setting or draft visibly invalidates the previous
result for export; Generate and Save recipe require explicit Apply of drafts.
Invalid or unapplied edits cannot be silently ignored. Export requires a current
result whose recipe matches the applied recipe and has no drafts. Loading a valid
recipe replaces the table, clears previous results, and resets layout to 312 px.
Invalid/old files preserve current applied state, drafts and results.

The Properties action area shows a compact **Unapplied changes** label with a
Fichte border/tint whenever either column or table drafts differ from applied
settings. Apply and Discard stay in stable, reachable positions outside the
scrolling field list. Both are disabled without drafts; exact reversion restores
that state and clears obsolete validation errors. A separate polite live region
announces only transitions, including table-only changes. Theme, view and
Properties resizing preserve drafts and this indication. Invalid Apply retains
the edits, pending treatment and specific error. Successful Apply clears the
draft indication while a prior result remains out of date until regeneration.
Recipe saving and output export remain separate from applying edits.

### Workbench interaction candidate (29–30 October 2026)

The separate UX review starts at integration commit
`eed69c60371ebeea0fa0faa17c11117ff7e04d9a`. It does not change generation,
the recipe formats or the live Render deployment.

Every Fields row is one selectable option: name, rule, applied summary and
remaining row area all select the same field. Interactive descendants are
excluded from row delegation; one activation must not also select a second
time. Selection stays in the list and updates Properties without applying or
discarding anything. Each field in the current table has its own draft form;
switching fields preserves all those drafts. Apply validates and commits all
changed field forms and table settings atomically. Failure preserves every
draft, the applied recipe and the prior result. Discard restores all current
table drafts together. Adding, duplicating, removing or switching tables still
requires applied/discarded drafts. All hidden drafts also block generation,
recipe saving and current-result export.

Fields uses a single-select listbox with manual selection: Tab enters at the
selected row, Up/Down moves focus, and Enter/Space selects. Tabs likewise use
Left/Right for focus and Enter/Space for activation. Home/End moves to either
edge of a group. One roving Tab stop per toolbar/group avoids a long sequence
of toolbar buttons; disabled/hidden actions are skipped. Normal editors retain
their arrow, Home/End, selection and modifier behavior. No new Apply/Discard
shortcut is registered. Escape closes the current popup or cancels an active
divider drag; it never globally discards drafts. Available keys are summarized
in the footer and Session help.

Actual pending settings have a slightly stronger label, a small dot and a light
Fichte tint; numeric values keep normal weight. Visible Draft text in Properties
and an accessible pending description complement the shape/weight distinction.
Unselected fields with saved drafts also show a dot beside their applied name.
Table name, Rows, Seed, Sample mode and the applicable primary-key editor use
the same treatment. Exact reversion, Apply and Discard remove only the pending
markers; applied-origin badges keep their separate meaning. A normal off→on→off
uniqueness toggle must return to the original unmodified state.

An actual new edit clears an obsolete success status. Relevant validation errors
remain until a participating setting changes or the drafts are discarded/reverted.
If validation identifies a different field, select that field and focus its
responsible input, without losing other drafts. The separate result status
continues to distinguish current, stale and absent output. Apply/Discard restore
the last visible edited input or the selected name fallback; successful Generate
returns focus to the active result tab only while the triggering action still
owns focus. Dialog cancellation returns to its trigger. Table headings/tabs stay
above their own scrollable result area at desktop sizes.

Single-table browser downloads derive a portable stem from the **applied** table
name: `test_measurements.csv`, `test_measurements.recipe.json` and the matching
`.run.json`. Normalize Unicode compatibility forms/case, replace punctuation,
spaces, separators and controls with underscores, collapse/trim separators and
bound the stem to80 characters. Empty/punctuation-only names use `table`; Windows
reserved device names receive a `table_` prefix. Linked-table CSV IDs, complete
dataset filenames and every serialized file's contents remain unchanged.

The source/browser implementation follows the W3C APG
[keyboard conventions](https://www.w3.org/WAI/ARIA/apg/practices/keyboard-interface/),
[listbox](https://www.w3.org/WAI/ARIA/apg/patterns/listbox/),
[manual tabs](https://www.w3.org/WAI/ARIA/apg/patterns/tabs/) and
[toolbar](https://www.w3.org/WAI/ARIA/apg/patterns/toolbar/) patterns. This is not
screen-reader, native OS-dialog or cross-platform accessibility certification.

After successful Apply or Discard, return focus to the last edited field,
including Rows or Seed when those alone changed. Field identity uses table,
column and setting keys, so refreshing Properties does not invalidate the
destination. If that setting disappears when discarding a rule change, use the
selected column's name, then Rows as a reachable fallback. Do not take focus
back after the user has moved on. Keep visible fields in place and scroll only
enough to reveal a clipped destination; failed Apply still focuses its error.

Editing an input involved in a reported validation error clears that historical
field message, its ARIA error state and its associated status. Either endpoint
can invalidate a prior Minimum/Maximum ordering error. A scalar parsing failure
belongs to its own input; unrelated edits and newer independent status errors
remain. Cross-input quota-total and unique-capacity errors track the inputs
used by those constraints. Clearing a historical error does not validate or
apply a draft: Apply still performs complete validation, pending remains and
exports stay blocked until the recipe/result is current.

## Reference established by hand

Before writing the engine, the three-row reference was fixed as:

| id | group | value |
| --- | --- | --- |
| 1 | demo | 10 |
| 2 | demo | 12 |
| 3 | demo | 14 |

IDs start at 1, group is constant `demo`, value is an integer sequence starting
at 10 with step 2, and all missingness is zero. Expectations are hand arithmetic,
not generator output. Random checks use independently derived bounds, types,
allowed categories, probability endpoints, zero-weight exclusion and broad
binomial tolerance; no self-generated snapshot is the statistical reference.
