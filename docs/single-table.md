# Explicit-rule single-table increment

This contract was established before implementation on 15 October 2026. It is a
bounded M1-01/M1-02 increment, not completion of M0 or M1. Sample profiling and
retain-and-extend follow next, then linked tables; both generic entry paths
remain required for the first usable release. Clinical derivations and binaries
are outside this batch. Several sequential implementation stages precede joint
maintainer review under the approved sequencing exception.

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
