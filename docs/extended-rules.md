# Bounded generic rules — version 3

Contract fixed before issue #14 implementation on 18 October 2026. This is a
generic rule contract, not the unreviewed clinical numeric policy. Existing
version-1 and version-2 recipes keep their semantics and output streams; they
are not silently migrated. New rules/uniqueness use `ravel-single-table/3`.
The app upgrades an in-memory copy only when the user applies such a rule;
saved input files are never overwritten. Older readers reject new versions.
Source-aware version 3 retains the version-2 embedded CSV/binding contract.

All existing limits, canonical 1 MiB saved-size checks and atomic failures still
apply. New rules use the existing independent field value/missingness streams.

| Rule | Parameters and exact semantics |
| --- | --- |
| `normal` | Decimal-text `mean` within ±10^12, positive `sd` ≤10^12, integer `places` 0–6. Python `Random.gauss` produces binary64 draws. Convert each draw's shortest decimal representation to Decimal and round half-even to the declared scale. Reject nonfinite or raw/rounded values outside ±10^12; no clipping, resampling or truncated-normal claim. |
| `boolean` | Decimal-text `probability` 0–1; independent Bernoulli true draws. Typed result is Boolean; CSV/preview spell exactly `true`/`false`. Missingness remains a separate independent probability. |
| `date` | Strict ISO `YYYY-MM-DD` `minimum`/`maximum`, valid dates in years0001–9999. Uniform whole days over the inclusive interval. No time/timezone/imputation. |
| `date_sequence` | Strict ISO `start` and integer day `step` (−36600…36600). Row i is start+i×step days; preflight the final endpoint against years0001–9999. Zero/negative steps are supported. |
| `category_quota` | Distinct nonempty `values`, nonnegative integer `counts`, nonnegative integer `missing_count`, `scope`=`generated` or `final`. Their sum must equal the declared scope count. Shuffle the exact multiset using this field's value stream. `missing_probability` must be0; missing cells are the explicit exact bucket. Probabilities are a different rule, not reinterpreted as counts. |

`unique: true` is supported for integer ticks, decimal ticks, uniform dates and
the inherently unique integer/formatted ID rules. Missing probability must be0.
Other combinations fail explicitly, including normal, category probability,
Boolean, sequence and quota uniqueness. A quota of1 per category may independently
produce a unique result without a separate uniqueness promise. Preflight
capacity before drawing; sample finite-domain ranks without replacement, never
retry until success. Version3 may record `unique: false` for other rules.

For retain-and-extend, uniqueness concerns the final table. Retained cells must
be nonmissing, parse as the declared scalar and be distinct by typed value;
lexical variants of the same number are duplicates. Retained values outside
the generator's new-row range stay intact. Exclude any retained values within
that domain before sampling new ones. Generated-only uniqueness concerns new
rows; identifier collision checks against source remain mandatory in both modes.

For `scope=generated`, quota totals apply only to newly generated rows. For
`scope=final`, totals include retained originals; subtract each original category
and exact-empty missing cell. A retained value outside the declared categories,
or an original count already above its quota, fails before successful output.
An added field has missing cells on retained rows. Never change original cells
to satisfy a quota. A zero-new extension still validates final quotas.

## Hand references fixed before implementation

- Date sequence: 2024-02-28, step1, count3 → 2024-02-28, 2024-02-29, 2024-03-01.
  Reverse start2024-03-01/step−1 reverses those dates. A singleton uniform
  interval2024-02-29…2024-02-29 produces only leap day. Reject2023-02-29 and
  stepping beyond9999-12-31.
- Boolean p0 is alwaysfalse; p1 is alwaystrue, independently of seed. A zero-weight
  category remains impossible under the existing category probability rule.
- Unique integer domain7…9 has capacity3: three rows contain exactly{7,8,9},
  four fail. Unique decimal1.0…1.2/places1 has exactly{1.0,1.1,1.2}; dates
  2024-02-28…2024-03-01 have exactly the three days above. With retained7,8,
  one new integer9 succeeds; two new values in7…9 fail.
- Quota A2/B1/missing1 over four generated rows has exactly those counts;
  shuffled order is not a hand reference. For source A,A,B,empty and final
  target A3/B2/missing1 over six total, residual new counts are A1/B1/missing0.
  A final A1 quota fails because two original A values already exist.
- Normal output rounding examples: decimal1.245 at places2→1.24;
  1.255→1.26; −1.245→−1.24. These explain half-even, not expected random draws.

## Statistical reference fixed before any statistical run

Seeds are **17, 42, 101, 2026, 65537**, selected now and unchanged after results.
At n=100,000 per seed, use the unchanged plan R5 thresholds: standard-normal
absolute mean≤0.02 and sample SD0.98–1.02; Bernoulli(p0.30) proportion0.29–0.31.
Use six decimal places for the normal fixture. Report every seed's actual
statistics and any failure; do not tune seeds/tolerances. The Gaussian-pair
correlation fixture is outside #14, so these checks do not pass overall R5.

Verify save/reload/seed stability, independent-field addition, actual preview/CSV,
actionable UI/CLI errors and atomic impossible requests. Human review remains
required; actual results belong in progress.json and the development guide.
