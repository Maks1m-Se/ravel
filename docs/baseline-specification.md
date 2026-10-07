# Proposed baseline and change specification

M0-05 proposal for the fictional clinical template; all additional policies
below await maintainer approval. This is a reviewable specification and three
hand-worked reference cases, not runnable clinical functionality or a stable
schema. It is separate from the accepted [recipe architecture and generic
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

## Proposed policies for approval

The initial template has one explicitly identified fictional treatment per
subject and a declared set of biomarker parameters. Inputs identify subjects,
record IDs, record kind, parameter/treatment, timestamp, value and unit. These
are logical requirements; field names remain illustrative. Input ordering and
visit labels do not determine eligibility. Preserve source record IDs for
traceability to the selected dose, selected baseline and each change target.

| Topic | Proposed policy | Reason and meaningful alternative |
| --- | --- | --- |
| Actual dose | Use only exposure records explicitly marked actually administered for the selected treatment. Each must have a finite positive amount and supported timestamp/unit. Select the earliest instant per subject, independent of biomarker parameter. Planned or explicitly not-administered doses cannot substitute. A missing/unknown administration status is invalid. | Prevent inferred dosing. Zero doses or multiple treatment regimens would require separately reviewed meanings rather than assuming they are actual treatment. |
| Missing actual dose | If no actual administration is recorded, baseline and change are missing with `NO_ACTUAL_DOSE`. An actual-dose record with a missing or malformed timestamp/amount is invalid, not equivalent to no dose. | A declared absence is a valid unusual scenario; incomplete actual-dose records can conceal an earlier dose. Alternative: reject all undosed subjects, which would exclude a planned reference case. |
| Time representation | Require complete date/time to whole seconds with `Z` or an explicit numeric UTC offset, e.g. `2026-01-01T10:00:00Z` or `2026-01-01T12:00:00+02:00`. Compare UTC instants. Reject missing/date-only timestamps, implicit local zones, fractional seconds and leap-second notation; never impute, round or truncate. | Equal instants remain equal despite offset spelling; absent precision cannot imply ordering. Alternatives: explicitly supported subsecond precision or reviewed partial-date bounds in a later template version. |
| Measurement eligibility | Within the subject and biomarker parameter, consider finite numeric, nonmissing measurements at instants strictly before the selected dose. Numeric zero is eligible. A missing value is explicit `null` and is skipped for baseline; an absent value field, text value, NaN or infinity is invalid. IDs, subject, parameter, timestamp and unit remain required even for a null value. | Do not select a later null value over an earlier usable value, or silently discard malformed records. Visit labels have no priority over observed time. |
| Equal-dose boundary and follow-up | A measurement exactly at dose is not baseline-eligible. Propose change targets only strictly after dose; an exactly-at-dose record remains in source data with `AT_DOSE_BOUNDARY`, without change. Pre-dose records remain source records and do not receive follow-up change. | Baseline exclusion is required by the plan. Follow-up exclusion at equality is an additional conservative choice awaiting approval; allowing an at-dose record as a change target is an alternative requiring explicit approval. |
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
empty collection provides no eligible baseline. The proposal does not infer
additional measurements, dosing times or visit schedules.

## Missing results and errors

For every declared subject/biomarker group, report the selected dose ID and
baseline ID/value when available. For each post-dose measurement, report its
ID, baseline reference, change and explicit missing-result reason when needed.
Nulls never become zero. A selected baseline is reused for that group's
post-dose measurements, with arithmetic in the declared biomarker unit.

| Valid situation | Proposed result and reason |
| --- | --- |
| No recorded actual dose | Baseline ID/value and changes are null: `NO_ACTUAL_DOSE`; do not classify observations as post-dose without a dose |
| Dose known, no eligible nonmissing baseline (including no measurements) | Baseline ID/value and any follow-up changes are null: `NO_ELIGIBLE_BASELINE` |
| Baseline exists, post-dose value is null | Keep baseline ID/value; change is null: `MISSING_FOLLOWUP_VALUE` |
| Dose and baseline known, no post-dose measurement | Report `NO_FOLLOWUP_MEASUREMENT` at group level; preserve baseline and create no invented follow-up row |

Reasons can coexist: report group-level absence of baseline or follow-up and
record-level null follow-up values separately. If dose is absent, use
`NO_ACTUAL_DOSE` first and do not assert pre-/post-dose classification. If
baseline is absent and a post-dose value is also null, its primary change
reason is `NO_ELIGIBLE_BASELINE`, with `MISSING_FOLLOWUP_VALUE` additionally
reported. At-dose classification is independent of group-level baseline absence.

Invalid input produces a clear error identifying the policy, record IDs and
subject/parameter context. **Error scope is the whole requested run**, across
all subjects and parameters: return no successful partial datasets or derived
outputs, and leave original inputs unchanged. A diagnostic report may identify
multiple errors but must label the run failed. Valid missing results are
explicit scenario outcomes, not validation errors. These behaviors also need
maintainer review before acceptance.

## Three invented, hand-worked cases

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
C3-M1 retains `AT_DOSE_BOUNDARY` under the additional proposed follow-up policy.
This is a valid unusual case with missing results, not a run error.

The cases contain **10 input records: 3 actual doses and 7 measurements**.
These expectations were established directly from the stated rules and hand
arithmetic before any derivation implementation. AI drafting, structural checks
and a second-agent document review are not independent clinical validation.
The other planned reference cases, R comparisons and targeted wrong-derivation
checks remain future work; no release gate is established by these examples.

## Required maintainer review

No clinical try-out command exists. Review this document rather than running
the tracking tools as though they validate clinical behavior:

1. Approve or revise actual-dose recognition, positive amount, absent-dose
   handling and whole-run failure for incomplete/invalid actual-dose records.
2. Approve or revise whole-second, offset-aware timestamps; strict equality;
   no imputation/rounding; latest-candidate and earliest-dose tie errors; and
   the additional strictly post-dose follow-up policy.
3. Approve or revise exact declared units, unsupported conversion, explicit
   null versus malformed values, missing-result reasons and error scope.
4. For Cases 1–3, identify dose and baseline records by hand and confirm
   **10 / +3**, **8 / +3**, and **null / null with NO_ELIGIBLE_BASELINE**.
   Record any corrections or acceptance before M0-05 can be marked done.
