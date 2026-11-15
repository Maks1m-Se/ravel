# Optional clinical template: preparation for review

Issue #16, 18 October 2026. **Proposal, not an adopted numeric policy or an
implemented clinical generator.** The accepted fictional policies and their
8 October acceptance remain in [baseline-specification.md](baseline-specification.md).
This preparation does not change them. Clinical numeric implementation waits
for maintainer review of the choices below; generic work and private packaging
can continue. No clinical or standards validation is claimed.

## One app, explicit domain selection

The same Home > Use template entry will list a clinical template only after its
planner, validator, derivation and reference checks are runnable. Today the only
listed template is Devices / measurements. Clinical-looking field names never
select a module. There is no public plugin loader or second clinical application.

The future explicit envelope will name a template and a policy version, e.g.
`clinical-baseline/1` and an adopted numeric-policy ID. This is a proposed module
request, **not another currently loadable recipe format**. Unknown or unimplemented
versions must fail before generation. Ordinary `ravel-dataset/1` remains generic.

| Logical input | Generic core responsibility | Clinical module responsibility |
| --- | --- | --- |
| Subjects | Stable subject table/key and bounded row count | Selected fictional treatment and explicitly declared subject/parameter pairs |
| Exposures | Stable exposure key, subject FK and explicit child counts | Actual/planned/not-administered status, positive amount, exact dose unit, whole-second offset-aware instant and earliest actual-dose selection |
| Measurements | Stable measurement key, subject FK, typed scalar values and explicit counts | Parameter declaration, pair membership, exact unit, eligible null versus malformed value, instant and baseline/change semantics |
| Declarations | Carry explicit configuration without guessing | Treatment/parameter registries and unit declarations; no Cartesian expansion of known subjects and parameters |
| Outputs | Serialize datasets/recipe/dictionary/run checksums without changing values | Group results, strictly post-dose changes and separate source-ID diagnostics; whole-run failure on invalid clinical input |

The generic core currently supports one parent per child, scalar keys, fixed
children-per-parent and literal text columns. It does not enforce compound
subject/parameter membership or understand treatment time. The clinical planner
will construct the supported structural requests and explicit record schedules;
subject-specific schedules and supplied record collections need a deliberately
specified adapter before implementation. They are not features of the current
linked generator. A template must not silently relax a structural constraint to
make a clinical scenario possible.

Small internal boundary, proposed rather than implemented:

1. `prepare(explicit_template_request, adopted_policy)` returns a generic engine
   request plus immutable clinical declarations/mapping, or actionable errors.
2. The generic engine validates/generates structural source tables. Stable source
   IDs and the untouched source values accompany the clinical input adapter.
3. `validate(source_tables, clinical_config, adopted_policy)` returns all
   independently evaluable failures, checks marked `NOT_EVALUATED` with their
   unavailable prerequisites, and a whole-run passed/failed status. Generic
   failures remain mandatory and cannot be allowed by a negative-fixture manifest.
4. `derive(validated_input, adopted_policy)` is available only after successful
   validation. It returns the three accepted logical collections and provenance.
   Failed validation returns zero successful group/change outputs across the run.
5. A separately explicit expected-invalid source-fixture export carries its
   scenario manifest and failed clinical status. Matching expected failures does
   not turn clinical validation into success. Export itself never derives values.

The reviewed recipe, source checksum, module/policy version, selected dose,
baseline and target source IDs must be recorded with results. No external API
stability is promised by these illustrative function/field names.

## Numeric policy proposed for review

These choices apply only to the future fictional clinical template. Existing
generic version1/2/3 numeric behavior remains as documented. The proposed limits
are software bounds, not medically meaningful ranges.

| Decision | Proposed rule | Consequence |
| --- | --- | --- |
| Input representation | Decode JSON numeric tokens directly to exact decimal values, preserving the original token separately. Reject Boolean, numeric text, NaN/infinity and absent required fields. Only explicit measurement `null` means missing. | `0.3` is exact decimal three tenths; `"0.3"` is invalid. No binary64 round trip during decoding. |
| Supported source scale/range | Nonmissing measurement absolute value at most1,000,000,000, at most six fractional decimal places after exact normalization. Nonnull dose amount has the same scale/upper bound and must be strictly positive. Reject excess precision/range rather than round input. | `1e-6` is valid; `1e-7` fails. Zero measurement is valid; zero actual dose fails. Planned/not-administered null amounts retain the accepted meaning. |
| Arithmetic | Store exact decimal coefficients at a declared six-place scale, or an equivalent exact Decimal representation. Perform subtraction exactly with sufficient checked precision; no intermediate rounding, overflow fallback, clipping or resampling. | Source coefficients are bounded by10^15 micro-units; deltas by2×10^15, within the proposed ±2,000,000,000 result range. A future operation exceeding its declared range fails the whole clinical run. |
| Output scale/rounding | Canonical clinical numeric CSV fields have six fractional digits, decimal point, no exponent/grouping, normalized positive zero. Baseline/change subtraction under these bounds is already exact at this scale. If a later reviewed operation needs quantization, round once at its declared output boundary, half to even. | `0.3−0.2` exports `0.100000`; missing exports an empty numeric cell with an explicit reason elsewhere. Source tokens remain in source/provenance; export never rewrites input. |
| Time | Retain the accepted whole-second ISO timestamp and explicit-zone policy; compare UTC instants exactly, with no tolerance or time rounding. | Offset-equivalent instants tie. Date-only, fractions and leap seconds remain invalid. |
| Python/R reference | Prefer exact comparison of exported six-place decimal coefficients/strings; parse CSV as character before independent reference conversion. IDs, selected references, row cardinality, null/reason sets, units and time order compare exactly. A secondary binary64 numeric comparison uses absolute tolerance5×10^-7 and relative tolerance0 over the bounded range. | At this range binary64 parse/subtraction error is below half a six-place unit. Relative tolerances could hide material fixed-scale errors on large values. A one-micro-unit wrong answer must fail the exact primary check. Missing values never participate in numeric tolerance. |

For an independent R implementation, decimal-character coefficient parsing into
integer-valued doubles is exact for these bounded coefficients (below2^53);
do not use R's 32-bit integer storage for micro-units. Derive reference results
independently from the source records, not from Python's selected IDs or deltas.
The tolerance proposal must be checked with boundary fixtures in M2-02 before
adoption; it is not evidence that Python/R comparison has run.

Hand calculations to review:

| Input / operation | Proposed result |
| --- | --- |
| `0.3−0.2` | Exact0.1; CSV `0.100000` |
| `1.000001−1.000000` | Exact0.000001; CSV `0.000001` |
| `1000000000−(-1000000000)` | Exact2000000000; CSV `2000000000.000000`, at the result bound |
| Source `1000000000.000001` or `0.0000001` | Reject range or excess scale, no clipping/rounding |
| Future half-even quantization to two places:1.245 /1.255 /−1.245 | 1.24 /1.26 /−1.24; illustrative only, not a current clinical derivation |
| Baseline0, follow-up2 | Baseline remains eligible; change2, not a missing baseline |

## Hand-checkable review sheet and fixture mapping

[baseline-four-cases.json](../examples/clinical-review/baseline-four-cases.json)
transcribes the accepted four cases:14 input records (four actual doses, ten
measurements), four group results and four change rows. It is a reference sheet,
not generator output or a current recipe. Each case is independent.

| Case | Selected dose / baseline | Required change | Boundary / failure check |
| --- | --- | --- | --- |
| C1 | C1-D1 / C1-M1=10 | C1-M2:13−10=3 | Ordinary strict pre-dose selection |
| C2 | C2-D1 / C2-M1=8 | C2-M3:11−8=3 | Later null C2-M2 is skipped, never imputed |
| C3 | C3-D1 / null | C3-M2:null, NO_ELIGIBLE_BASELINE | C3-M1 at dose has AT_DOSE_BOUNDARY and no change row |
| C4 | C4-D1 / C4-M1=10 | C4-M3:15−10=5 | No C4-M2 change. Wrong inclusive follow-up adds2; wrong inclusive baseline changes result to3. |

[negative-illustrations.json](../examples/clinical-review/negative-illustrations.json)
transcribes accepted illustrations a–c and the crossed-pair counterexample.
Failure matching is exactly by code, scope and complete source-ID set.
`NOT_EVALUATED` entries are separate, never additional expected failures:

- Bad unit on A-M2 suppresses eligibility/selection/tie evaluation for that
  group; no fallback to A-M1 and no invented BASELINE_TIE failure.
- B-M1/B-M2 form a valid latest-eligible tie; both source IDs are required.
- Malformed actual-dose time C-D1 suppresses dose selection/tie and all
  dose-dependent checks. It cannot become NO_ACTUAL_DOSE; C-M1's independent
  record checks still run.
- Known subject S-A and parameter BX-2 with undeclared pair (S-A,BX-2)
  fails UNDECLARED_GROUP for X-M1; it never creates another group.

Future tests additionally map the accepted empty group, undosed group, null
follow-up, zero baseline, positive/invalid dose, equal UTC instants with different
offset spelling, earliest-dose tie, invalid ineligible record, unknown status,
and exact-unit failure dependencies from the baseline specification. These do
not establish the remaining twelve-case suite or selected standards mappings.

[structure-only.recipe.json](../examples/clinical-review/structure-only.recipe.json)
is a runnable **generic** three-table structural example. Its clinical-looking
names and literal `baseline` text do not select clinical code. It is not a
clinical template and does not exercise derivations. The separate JSON review
sheets are deliberately rejected by the application recipe loader.

Review required before clinical numeric implementation: approve or amend the
range/scale, exact representation, overflow, six-place export and comparison
rules above, then assign an adopted policy ID. Review the fixture transcription
against the accepted source and the proposed adapter/interface boundary. This
prerequisite is recorded in progress.json; no review has been assumed.
