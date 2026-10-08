# Baseline and change specification

The maintainer accepted M0-05's policies, validation/output contracts and four
hand-worked reference cases on 8 October 2026 as a fictional test-data
specification, following the Hub's final document review. Acceptance establishes
neither standards conformity, implemented functionality nor independent clinical
validation. Numeric decisions remain subject to the recorded M1/M2 prerequisites;
field notation and schema stability remain unresolved. This specification is
separate from the accepted [recipe architecture and generic
structural example](specification.md). Clinical meaning belongs in the bundled
clinical module and requires explicit clinical template/version selection.

## Preserved rule

The unchanged **Clinical specification** paragraph in [the plan](plan.md)
requires selection, within subject and parameter, of the last nonmissing
measurement strictly before the first actual dose. Change is follow-up minus
baseline in compatible units. No eligible baseline means missing baseline and
change with an explicit reason. Ties need a declared rule or a clear error.
This is this fictional project's rule, not a universal clinical convention or
a claim of standards compliance. Selected standards mappings remain M2 work.

## Source context and scope

Inspected on 8 October 2026:

- [CDISC SDTMIG v3.3 HTML](https://www.cdisc.org/standards/foundational/sdtmig/sdtmig-v3-3/html),
  for SDTM v1.7: §4.5.9 distinguishes the operational pre-treatment reference
  flag `--LOBXFL`, sponsor-defined `--BLFL`, and SAP-defined analysis baseline
  flag `ABLFL`. They need not select the same record. §§4.4.1–4.4.2 describe
  ISO 8601 character date/time representations, including partial precision,
  optional fractional seconds and optional timezones.
- [FDA Study Data Technical Conformance Guide, June 2026, v6.2.1](https://www.fda.gov/media/153632/download):
  §4.1.2, “Numeric Date Variables” (printed p18 / PDF p31), discusses numeric
  analysis dates/times, documenting software reference dates, SAP-directed
  partial-date imputation with flags, and retaining character dates for
  traceability. §4.1.4.1 (printed p36 / PDF p49) distinguishes CDISC and Agency
  requirements, addresses null derivations when required data are absent, and
  gives last-nonmissing pre-first-dose baseline selection as an example.

The requested HTML sections and PDF text were accessible. PDF image inspection
was unavailable: the browser screenshot tool returned no rendered image data.
The numeric-date subsection is cited by title within §4.1.2 because the extracted
text did not retain its subsection number. This is a targeted source check,
not a review of every requirement in either publication.

These standards/guidance statements provide context, not a universal baseline
definition. Strict pre-dose selection and TX-1/BX-1 are fictional study
assumptions. Positive-dose-only treatment recognition, whole-second timestamps
with explicit offsets, tie errors and unsupported unit conversion are scoped
software choices accepted below for this fictional template. The broader source
formats do not require those restrictions. No clinical or submission compliance is claimed; selected
standards mappings remain M2 work.

## Accepted policies for the fictional template

The initial template has one explicitly identified fictional treatment per
subject and a declared set of biomarker parameters. Inputs identify subjects,
record IDs, record kind, parameter/treatment, timestamp, value and unit. These
are logical requirements; field names remain illustrative. Input ordering and
visit labels do not determine eligibility. Preserve source record IDs for
traceability to the selected dose, selected baseline and each change target.

Every measurement's `(subject, parameter)` pair must be explicitly declared.
Knowing the subject and parameter individually is insufficient: do not expand
their Cartesian product or create groups from measurements. An undeclared pair
fails with `UNDECLARED_GROUP`, identifying the source ID and supplied pair.

| Topic | Accepted policy | Reason and meaningful alternative |
| --- | --- | --- |
| Actual dose | Use only exposure records explicitly marked actually administered for the selected treatment. Each must have a finite positive amount and supported timestamp/unit. Select the earliest instant per subject, independent of biomarker parameter. Planned or explicitly not-administered doses cannot substitute. A missing/unknown administration status is invalid. | Prevent inferred dosing. Zero doses or multiple treatment regimens would require separately reviewed meanings rather than assuming they are actual treatment. |
| Missing actual dose | If no actual administration is recorded, baseline and change are missing with `NO_ACTUAL_DOSE`. An actual-dose record with a missing or malformed timestamp/amount is invalid, not equivalent to no dose. | A declared absence is a valid unusual scenario; incomplete actual-dose records can conceal an earlier dose. Alternative: reject all undosed subjects, which would exclude a planned reference case. |
| Time representation | Require complete date/time to whole seconds with `Z` or an explicit numeric UTC offset, e.g. `2026-01-01T10:00:00Z` or `2026-01-01T12:00:00+02:00`. Compare UTC instants. Reject missing/date-only timestamps, implicit local zones, fractional seconds and leap-second notation; never impute, round or truncate. | Equal instants remain equal despite offset spelling; absent precision cannot imply ordering. Alternatives: explicitly supported subsecond precision or reviewed partial-date bounds in a later template version. |
| Measurement eligibility | Within the subject and biomarker parameter, consider finite numeric, nonmissing measurements at instants strictly before the selected dose. Numeric zero is eligible. A missing value is explicit `null` and is skipped for baseline; an absent value field, text value, NaN or infinity is invalid. IDs, subject, parameter, timestamp and unit remain required even for a null value. | Do not select a later null value over an earlier usable value, or silently discard malformed records. Visit labels have no priority over observed time. |
| Equal-dose boundary and follow-up | A measurement exactly at dose is not baseline-eligible. Change targets are only strictly after dose; report `AT_DOSE_BOUNDARY` in separate diagnostics keyed by the measurement's source ID, with no change row. Source records remain unchanged. Pre-dose records do not receive follow-up change. | Baseline exclusion is required by the plan. Follow-up exclusion at equality is an accepted conservative choice for this template; allowing an at-dose record as a change target would require a separately reviewed policy change. |
| Ties | Reject two or more actual-dose records tied at the earliest dose instant, or two or more nonmissing measurements tied at the latest eligible baseline instant for a subject/parameter, even if their numeric values agree. Report all competing IDs. Do not use input order or record ID as a clinical tie-break. | An explicit error avoids arbitrary provenance. Alternatives: an approved replicate rule or dose-event consolidation; neither is selected here. Earlier baseline-candidate ties do not affect a later unique selection. Separate follow-up records are evaluated by ID rather than collapsed. |
| Units and conversion | Each biomarker parameter declares one fictional unit; all its records, including null-valued and ineligible records, must use exactly that unit. Treatment amounts use a separately declared dose unit. Units are not compared across different parameters. Unit conversion, aliases and scaling are unsupported; mismatches are invalid. | No guessed equivalence or silent conversion. Alternative: a reviewed conversion table with explicit factors, applicability and independent reference results in a later version. |

Illustrative record kinds `actual-dose`, `planned-dose`, `not-administered` and
`measurement` explicitly encode administration/measurement status. Planned or
not-administered exposure records still require valid IDs, references, complete
timestamps and the declared treatment unit; their amounts may be null, otherwise
must be finite and positive. Their timestamps describe planned or recorded
non-administration events, never actual dosing. They cannot establish a dose.

Validate all submitted records before deriving results, including those that
would be ineligible. Unknown subject/parameter/treatment references, duplicate
record IDs, unsupported record kinds and violated policies are invalid. A
missing biomarker measurement collection is allowed for a declared group; an
empty collection provides no eligible baseline. The specification does not infer
additional measurements, dosing times or visit schedules.

## Logical outputs and valid missing results

For a valid run, produce three logical collections; their field notation and
output ID spelling are illustrative, not a stable schema:

- **Group results:** exactly one row per explicitly declared subject/parameter
  pair, even with zero measurements. Identify the group, selected dose ID/time,
  baseline source ID/value/unit (null when absent), and group-level reasons.
  Do not infer groups only from observed measurement rows.
- **Changes:** exactly one row per measurement strictly after the selected
  dose, including null-valued measurements. Identify the output, group, target
  source ID, baseline source ID, change/unit and missing-result reasons. Reuse
  that group's baseline. No dose means zero change rows; pre-dose and at-dose
  measurements receive none. Never invent a follow-up row. Nulls never become
  zero.
- **Record diagnostics:** keyed by source record ID, with code and group
  context; keep these separate from source records. `AT_DOSE_BOUNDARY` belongs
  here for each measurement equal to the dose instant. With no dose, put
  `NO_ACTUAL_DOSE` on the group and on each of its measurement diagnostics;
  do not classify those measurements as pre-dose, at-dose or post-dose.
  Missing change reasons also identify their target source ID here. These
  valid-outcome diagnostics are distinct from validation failures.

| Valid situation | Specified result and reason |
| --- | --- |
| No recorded actual dose | Group dose and baseline ID/value are null: `NO_ACTUAL_DOSE`; zero change rows, with the same code on each measurement diagnostic |
| Dose known, no eligible nonmissing baseline (including no measurements) | Baseline ID/value and any follow-up changes are null: `NO_ELIGIBLE_BASELINE` |
| Baseline exists, post-dose value is null | Keep baseline ID/value; change is null: `MISSING_FOLLOWUP_VALUE` |
| Dose known, no post-dose measurement, whether or not baseline exists | Report `NO_FOLLOWUP_MEASUREMENT` at group level; preserve any baseline and create no invented follow-up row |

When dose exists, evaluate baseline absence and follow-up absence independently:
a group can report both `NO_ELIGIBLE_BASELINE` and `NO_FOLLOWUP_MEASUREMENT`.
A post-dose record with null value is a follow-up record, so it does not cause
`NO_FOLLOWUP_MEASUREMENT`. Report its null value separately. If dose is absent, use
`NO_ACTUAL_DOSE` first and do not assert pre-/post-dose classification. If
baseline is absent and a post-dose value is also null, its primary change
reason is `NO_ELIGIBLE_BASELINE`, with `MISSING_FOLLOWUP_VALUE` additionally
reported. At-dose classification is independent of group-level baseline absence.

Two auxiliary illustrations (not part of the numbered case record count):

- **Empty measurement group:** declare `(S-EMPTY, BX-1)`. Its only input is
  `E-D1`, actual-dose, S-EMPTY, TX-1, `2026-01-01T10:00:00Z`, value 1,
  `dx-unit`. Output `E-G1` has dose E-D1, null baseline ID/value, and both
  `NO_ELIGIBLE_BASELINE` and `NO_FOLLOWUP_MEASUREMENT`. There are zero change
  rows and no record diagnostics: absence belongs to the declared group.
- **Undosed group:** declare `(S-UNDOSED, BX-1)` with no exposures. Its only
  input is `U-M1`, measurement, S-UNDOSED, BX-1, `2026-01-01T11:00:00Z`, value
  10, `bx-unit`. Output `U-G1` has null dose/baseline ID/value and group reason
  `NO_ACTUAL_DOSE`; diagnostics map U-M1 to `NO_ACTUAL_DOSE`. There are zero
  change rows. Without a dose anchor, do not additionally assert baseline or
  follow-up absence.

## Invalid inputs and declared negative fixtures

Clinical validation reports a clear error identifying the violated policy,
source IDs and subject/parameter context. **Failure scope is the whole requested
clinical run**, across all subjects and parameters: no successful group results,
change outputs or partial derived datasets. A separate diagnostic report may
identify multiple failures, but labels the run failed and leaves inputs intact.
Valid missing results above are explicit outcomes, not validation failures.

### Validation dependencies and failure codes

Apply this procedure, independent of input row order:

1. Run every applicable generic and record-level clinical check. Report every
   independently evaluable failure; one bad field does not hide another failure
   whose prerequisites are available. For example, a bad timestamp does not
   prevent checking a known parameter's unit or a supplied numeric value.
   A check needing an unavailable declaration or unparseable field is not
   evaluable; do not guess its input. Generic validation remains mandatory.
2. Establish a subject's dose anchor only if all its actual-dose records pass
   validation. Any failed actual-dose record suppresses dose selection,
   earliest-dose tie checking and all dose-dependent checks for that subject;
   do not discard it and select from a reduced set. Otherwise, an earliest-dose
   tie fails and prevents an anchor. Neither condition means `NO_ACTUAL_DOSE`.
   That valid absence applies only when absence of actual dosing was established
   without a failed prerequisite. An identifiable exposure with missing/unknown
   administration status also blocks that subject's anchor, even if another
   valid actual-dose record exists: it could conceal an earlier administration.
3. For each declared subject/parameter group, baseline eligibility, selection
   and latest-baseline tie checking require a valid dose anchor and all the
   group's measurements to pass record-level clinical validation, even records
   that would appear ineligible. A failed measurement suppresses those checks
   for the entire group: **no fallback baseline from a reduced set**. An invalid
   record is not an eligible/noneligible decision or `NO_ELIGIBLE_BASELINE`.
   An undeclared pair never creates another group to evaluate.
4. Continue independent record checks and checks in unaffected subjects/groups.
   Time comparisons/classification require a valid dose anchor, declared group
   membership and a valid measurement timestamp; a baseline-dependent check
   additionally requires completed baseline selection. Any validation failure
   still suppresses all successful derived outputs for the whole run.

Report a check blocked by a validation failure separately as **NOT_EVALUATED**,
with its check name, affected scope/source IDs and failed prerequisites. It is
neither an additional failure nor a valid missing-result reason. Do not substitute missing outcomes
for an invalid anchor or invalid selection. Valid missing-result reasons belong
to successfully evaluated outcomes as described above, not to skipped checks.
A valid absence of dose follows `NO_ACTUAL_DOSE` with zero change rows; it is
not a failed-prerequisite diagnostic.

The following failure codes cover the accepted policies;
they are logical diagnostics, not a general validation framework or stable API.
Each failure identifies its affected scope and source IDs (all competing IDs
for a tie; no source ID when the failure is recipe-level).
Use subject scope for exposure failures and subject/parameter scope for
measurement failures; an undeclared pair is identified as the supplied pair,
not a new group. If references cannot identify such a scope, retain record or
recipe scope and report the unavailable dependent checks separately.

| Failure code | Check and affected scope |
| --- | --- |
| `GENERIC_VALIDATION_FAILED` | Mandatory recipe/schema/version, count/type/key/reference or declared generic-constraint check; identify the particular check and recipe/record scope. Generic failures are never permitted by a negative-fixture manifest. |
| `INVALID_RECORD_KIND` | Missing/unsupported clinical record kind; source record. |
| `INVALID_ADMINISTRATION_STATUS` | Missing/unknown exposure administration status; source record and identifiable subject. If kind encodes status, an unknown exposure status is this failure, not evidence of no dose. |
| `UNDECLARED_GROUP` | Both subject and parameter references are known, but their pair is not declared; source measurement and supplied pair. If a reference itself is unknown, report its generic reference failure; pair membership is not evaluated. |
| `INVALID_TIMESTAMP` | Missing, malformed or unsupported clinical timestamp/precision/zone; source record. |
| `INVALID_DOSE_AMOUNT` | Actual amount missing or not finite/positive, or a nonnull planned/not-administered amount not finite/positive; source exposure. |
| `INVALID_MEASUREMENT_VALUE` | Absent or nonnumeric/nonfinite measurement value; source measurement. Explicit null is valid. |
| `INCOMPATIBLE_UNIT` | Missing or nonmatching declared treatment/parameter unit; source record. Requires a known treatment/parameter and its unit declaration. |
| `EARLIEST_DOSE_TIE` | Multiple otherwise valid actual-dose records at the earliest instant; subject and all tied source IDs. |
| `BASELINE_TIE` | Multiple otherwise valid nonmissing measurements at the latest strictly pre-dose instant; declared group and all tied source IDs. |

Generic and clinical checks may identify different independently evaluable
violations on the same record; retain both with their check/scope/IDs. Do not
invent a clinical comparison when generic prerequisites are unavailable.

### Hand-checkable diagnostic illustrations

These are validation illustrations, separate from Cases 1–4 and their counts.
Assume no additional generic constraint is violated; timestamps and units can
be structurally valid strings while failing the clinical policies. All mandatory
generic checks still apply. These illustrations do **not** authorize exporting
a fixture that fails generic validation.

For a–c, declare `(S-DIAG, BX-1)` with fictional unit `bx-unit` and treatment
TX-1 with unit `dx-unit`. Each illustration is a separate input. Unless replaced
in c, dose `D-D1` is actual-dose, S-DIAG, TX-1, `2026-01-01T10:00:00Z`, value
1, `dx-unit`. Every listed measurement is for S-DIAG/BX-1.

| Illustration | Additional/replacement records | Required failures | Checks not evaluated |
| --- | --- | --- | --- |
| a — bad unit and simultaneous measurements | A-M1: measurement, `2026-01-01T09:00:00Z`, 10, `bx-unit`; A-M2: measurement, same timestamp, 12, `other-unit` | `INCOMPATIBLE_UNIT`, group (S-DIAG, BX-1), source A-M2 | Group baseline eligibility/selection and `BASELINE_TIE` check: A-M2 failed record validation. D-D1 still establishes the dose anchor; do not select A-M1 as a fallback. |
| b — valid latest-eligible tie | B-M1: measurement, `2026-01-01T09:00:00Z`, 10, `bx-unit`; B-M2: measurement, same timestamp, 12, `bx-unit` | `BASELINE_TIE`, group (S-DIAG, BX-1), sources B-M1 and B-M2 | Baseline-dependent checks: selection failed on the tie. Dose and eligibility checks were evaluated; the tie is a failure, not a skipped check. |
| c — malformed actual-dose time | Replace D-D1 with C-D1: actual-dose, S-DIAG, TX-1, timestamp `not-a-time`, value 1, `dx-unit`; C-M1: measurement, `2026-01-01T09:00:00Z`, 10, `bx-unit` | `INVALID_TIMESTAMP`, subject S-DIAG, source C-D1 | Dose selection/tie and all dose-dependent checks for S-DIAG. C-M1's independent record checks still pass. No invented anchor or `NO_ACTUAL_DOSE` outcome. |

In a, a manifest expecting both `INCOMPATIBLE_UNIT` and `BASELINE_TIE` does
not match: the tie check cannot be evaluated. In b the tie is required; in c
only the stated timestamp failure is required under the assumptions above.
Every illustration fails clinical validation and yields zero successful group
or change outputs; independent checks elsewhere still run.

**Crossed-pair counterexample (Claude review finding, illustrative IDs):**
declare subjects S-A/S-B and parameters BX-1/BX-2 (both use `bx-unit`), but only
pairs `(S-A, BX-1)` and `(S-B, BX-2)`. Input X-M1 is measurement, S-A, BX-2,
`2026-01-01T09:00:00Z`, value 10, `bx-unit`. Its individual references, value,
timestamp and unit are valid, but `(S-A, BX-2)` is not declared. Report
`UNDECLARED_GROUP`, scope (S-A, BX-2), source X-M1. Do not create a third group
or assign X-M1 to either declared group. No successful derived outputs are
emitted for the run.

### Declared negative-fixture contract

The plan's deliberately invalid scenarios require a separate contract for
creating a **declared negative source fixture** for testing:

1. The request explicitly identifies the intended clinical defects in its
   scenario manifest, including expected failure codes, affected scopes and
   source IDs. Such a labeled fixture may be generated and exported as test
   input. Its export must carry the manifest and expected-invalid clinical
   status; successful fixture creation is not successful clinical derivation.
2. Generic recipe/schema, counts, types, keys, references and declared generic
   constraints still have to pass. The manifest cannot waive them or silently
   relax a constraint. Clinical defects, such as a supported numeric measurement
   in a unit incompatible with its clinical parameter, belong to the clinical
   validator; the fixture must still be structurally valid. A declared generic
   temporal constraint also remains enforced even in a negative fixture.
3. Clinical validation must report the **failures required by the dependency
   procedure above** and suppress all successful derived outputs for that run.
   Unexpected defects remain failures. A test harness passes the expected-error
   check only when the actual failure set exactly matches the manifest by
   failure code, affected scope and source ID set, with no missing or extra
   failures. Skipped checks are not additional failures; declaring an error
   that cannot be evaluated does not satisfy an expectation. A passing harness
   never changes the failed clinical-validation status.

For example, a labeled fixture can request an incompatible-unit measurement
with an expected clinical unit error and retain/export that source record for
testing. The clinical run still fails for the unit error, with zero successful
group/change outputs. This preserves R2's manifest requirement and prohibition
on silent relaxation or successful partial output. Ordinary clinical generation
does not export an invalid dataset as a successful result. This contract is a
specification, not an implemented mode or a general defect-injection framework.

## Implementation ownership and unresolved numeric policy

Before clinical numeric implementation in **M1-01, Implement linked clinical CLI
slice** ([existing task record](progress.json)), specify and review arithmetic
representation and supported range/overflow handling, rounding (including when
it occurs and tie behavior), export formatting/precision, and Python/R comparison
tolerances. Align the tolerances with **M2-02, Verify derivations independently
in R**, and the plan's R3 cross-platform qualification. These remain unresolved;
the small exact-integer arithmetic below selects no floating-point/decimal
implementation or mandatory decimal-scale recipe attribute.

**M2-01, Establish twelve cases and selected mappings**, owns implementing the
specified clinical derivation outputs and declared negative-fixture
export/validation contract across the planned scenarios, with reference
expectations established before implementing their derivations. M2-02 requires
documented Python/R comparison tolerances consistent with the reviewed numeric
policy. These obligations are recorded in the existing [task criteria](progress.json);
they do not move the full scenario contract into M1 or expand its bounded slice.

## Four invented, hand-worked cases

Each case is separate. `kind=actual-dose` means administered treatment TX-1,
amount 1 in fictional `dx-unit`. `kind=measurement` means biomarker BX-1 in
fictional `bx-unit`. Each case declares its listed subject, TX-1 and BX-1.
All timestamps are UTC, to seconds. Dose amounts and biomarker values are
different quantities; no unit conversion or cross-parameter subtraction occurs.

### Case 1 — ordinary baseline

| Record ID | Kind | Subject | Parameter/treatment | Timestamp | Value | Fictional unit |
| --- | --- | --- | --- | --- | --- | --- |
| C1-M1 | measurement | S-C1 | BX-1 | 2026-01-01T09:00:00Z | 10 | bx-unit |
| C1-D1 | actual-dose | S-C1 | TX-1 | 2026-01-01T10:00:00Z | 1 | dx-unit |
| C1-M2 | measurement | S-C1 | BX-1 | 2026-01-01T11:00:00Z | 13 | bx-unit |

First actual dose: **C1-D1**. C1-M1 is nonmissing and strictly earlier;
it is the only eligible measurement. Selected baseline record: **C1-M1**,
baseline **10 bx-unit**. For C1-M2, change is **13 − 10 = +3 bx-unit**.
No missing-result reason applies. This is a valid ordinary case.

### Case 2 — latest pre-dose value missing

| Record ID | Kind | Subject | Parameter/treatment | Timestamp | Value | Fictional unit |
| --- | --- | --- | --- | --- | --- | --- |
| C2-M1 | measurement | S-C2 | BX-1 | 2026-01-01T09:00:00Z | 8 | bx-unit |
| C2-M2 | measurement | S-C2 | BX-1 | 2026-01-01T09:30:00Z | null | bx-unit |
| C2-D1 | actual-dose | S-C2 | TX-1 | 2026-01-01T10:00:00Z | 1 | dx-unit |
| C2-M3 | measurement | S-C2 | BX-1 | 2026-01-01T11:00:00Z | 11 | bx-unit |

First actual dose: **C2-D1**. C2-M2 is earlier than dose but missing, so it
cannot be baseline. C2-M1 is the latest nonmissing eligible measurement.
Selected baseline record: **C2-M1**, baseline **8 bx-unit**. For C2-M3,
change is **11 − 8 = +3 bx-unit**. The null source value stays null; it is not
imputed. This is valid with a missing source value and nonmissing derivations.

### Case 3 — strict boundary without an earlier eligible value

| Record ID | Kind | Subject | Parameter/treatment | Timestamp | Value | Fictional unit |
| --- | --- | --- | --- | --- | --- | --- |
| C3-D1 | actual-dose | S-C3 | TX-1 | 2026-01-01T10:00:00Z | 1 | dx-unit |
| C3-M1 | measurement | S-C3 | BX-1 | 2026-01-01T10:00:00Z | 12 | bx-unit |
| C3-M2 | measurement | S-C3 | BX-1 | 2026-01-01T11:00:00Z | 15 | bx-unit |

First actual dose: **C3-D1**. C3-M1 is exactly at dose, so `time < dose`
is false. C3-M2 is later; neither is baseline-eligible. Selected baseline
record: **none (null)**. Baseline and C3-M2 change are **missing (null)** with
`NO_ELIGIBLE_BASELINE`. Subtracting 12 from 15 would violate the strict boundary.
Separate diagnostics keyed by C3-M1 report `AT_DOSE_BOUNDARY` under the
accepted strictly post-dose follow-up policy; the source record is unchanged.
This is a valid unusual case with missing results, not a run error.

### Case 4 — boundary with an earlier eligible value

| Record ID | Kind | Subject | Parameter/treatment | Timestamp | Value | Fictional unit |
| --- | --- | --- | --- | --- | --- | --- |
| C4-M1 | measurement | S-C4 | BX-1 | 2026-01-01T09:00:00Z | 10 | bx-unit |
| C4-D1 | actual-dose | S-C4 | TX-1 | 2026-01-01T10:00:00Z | 1 | dx-unit |
| C4-M2 | measurement | S-C4 | BX-1 | 2026-01-01T10:00:00Z | 12 | bx-unit |
| C4-M3 | measurement | S-C4 | BX-1 | 2026-01-01T11:00:00Z | 15 | bx-unit |

First actual dose: **C4-D1**. Selected baseline record: **C4-M1**, baseline
**10 bx-unit**. C4-M2 is exactly at dose: diagnostics keyed by C4-M2 report
`AT_DOSE_BOUNDARY`, with no change row and no source modification. For C4-M3,
change is **15 − 10 = +5 bx-unit**. No group-level missing reason applies.
Incorrect inclusive follow-up (`time >= dose`) would produce an extra
**12 − 10 = +2** change at dose. Incorrect inclusive baseline (`time <= dose`)
would select C4-M2 and produce **15 − 12 = +3** after dose. This case makes the
two boundary mistakes separately observable.

### Expected logical output IDs and diagnostics

Each group below is the case's declared `(S-Cn, BX-1)` pair. An empty reason or
diagnostic list means none. Output IDs are illustrative, with source references
explicit so the expected structure can be checked by hand.

| Case | Group output ID | Dose ID | Baseline ID / value | Group reasons | Change output ID: target source ID / change / reasons | Record diagnostics keyed by source ID |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | C1-G1 | C1-D1 | C1-M1 / 10 | none | C1-CH1: C1-M2 / +3 / none | none |
| 2 | C2-G1 | C2-D1 | C2-M1 / 8 | none | C2-CH1: C2-M3 / +3 / none | none |
| 3 | C3-G1 | C3-D1 | null / null | NO_ELIGIBLE_BASELINE | C3-CH1: C3-M2 / null / NO_ELIGIBLE_BASELINE | C3-M1: AT_DOSE_BOUNDARY; C3-M2: NO_ELIGIBLE_BASELINE |
| 4 | C4-G1 | C4-D1 | C4-M1 / 10 | none | C4-CH1: C4-M3 / +5 / none | C4-M2: AT_DOSE_BOUNDARY |

Cases 1–4 contain **14 input records: 4 actual doses and 10 measurements**,
with four group outputs and four change outputs, including Case 3's null change.
There are no change outputs for C3-M1 or C4-M2. Case 4 extends the existing
exactly-at-first-dose coverage within the twelve planned scenarios; it does
not add a thirteenth scenario or change the release criteria.
These expectations were established directly from the stated rules and hand
arithmetic before any derivation implementation. AI drafting, structural checks
and a second-agent document review are not independent clinical validation.
The other planned reference cases, R comparisons and targeted wrong-derivation
checks remain future work; no release gate is established by these examples.

## Maintainer acceptance and review record

The maintainer's acceptance and the Hub's final document review are recorded
separately in [progress evidence](progress.json), dated 8 October 2026. Claude's
earlier reviews informed the preceding revisions; no review of the final
revision by Claude is asserted. The accepted review scope is retained below.
No clinical try-out command exists, and tracking checks do not validate clinical
behavior.

1. Actual-dose recognition, positive amount, absent-dose handling and whole-run
   failure; source distinctions between the fictional study rule, scoped
   software restrictions and standards context.
2. Whole-second, offset-aware timestamps; strict equality;
   no imputation/rounding; latest-candidate and earliest-dose tie errors; and
   the additional strictly post-dose follow-up policy.
3. Exact declared units, unsupported conversion, explicit
   null versus malformed values, output cardinality, separate diagnostics and
   independent baseline/follow-up absence checks, including the empty and undosed
   group illustrations.
4. Declared negative fixtures can be exported for testing while
   clinical validation still fails the whole run with no successful derived
   output; generic validation and unexpected-defect failures remain intact.
   The dependency procedure, failure codes and a–c diagnostic examples
   distinguish required failures, NOT_EVALUATED checks and valid missing reasons.
   Manifests match only evaluable failures by code/scope/source IDs. Declared
   pair membership rejects the crossed pair illustrated after Claude's review.
5. Cases 1–4 identify dose and baseline records and output IDs with results
   **10 / +3**, **8 / +3**, **null / null with NO_ELIGIBLE_BASELINE**,
   and **10 / +5**, including the at-dose diagnostics and absent change rows,
   and Case 4's incorrect **+2** / **+3** boundary alternatives.
6. The M1-01 numeric-policy prerequisite, M2-01 output/negative-
   fixture implementation ownership and M2-02 tolerance obligation. Numeric
   representation/range, overflow, rounding, formatting and tolerances remain
   unresolved; reference expectations precede their derivations. These later
   prerequisites remain required after M0-05 acceptance.
