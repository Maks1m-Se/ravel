# Optional clinical template: preparation for review

Issue #16, 18 October 2026, updated 15 November. **Pipeline proposal, not an
implemented clinical generator; numeric core separately adopted as
`clinical-numeric/1` (E85).** The accepted fictional policies and their
8 October acceptance remain in [baseline-specification.md](baseline-specification.md).
This preparation does not change them. Clinical numeric implementation waits
for a separately authorized task; generic work and private packaging
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
subject-specific schedules still need a planner. Supplied record collections
now have the bounded internal contract below. They are not features of the current
linked generator. A template must not silently relax a structural constraint to
make a clinical scenario possible.

The complete clinical pipeline below remains proposed. Only the explicit
source adapter and structural contract described later in this document are
implemented:

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

## Adopted numeric core and provisional comparison tolerance

**Core adopted by Maksim, 15 November 2026: `clinical-numeric/1` (E85).** The canonical
[numeric decision sheet and hand-worked boundaries](baseline-specification.md#numeric-policy-decision-sheet--adopted-core-policy)
refine this document's earlier E84 proposal. The adopted core retains exact
decimal interpretation, six effective fractional places, source magnitude
≤1,000,000,000 and exact subtraction bounded by ±2,000,000,000. Generic numeric
behavior and the lossless clinical source loader are unchanged.

The adopted core specifies JSON exponent syntax, negative-zero handling,
trailing-zero normalization, rejection rather than input rounding, nulls,
fixed-six-place CSV and exact primary comparison. It removes any suggestion
that a future half-even quantization rule is already authorized for this
subtraction-only policy. The optional secondary absolute tolerance5×10^-7,
relative tolerance0, is derived conditionally for binary64 diagnostics only;
actual R/SAS checks and acceptance remain pending. It cannot override an exact
comparison failure. See the canonical sheet for the independent integer boundary
calculations, assumptions and trade-offs. The secondary tolerance is excluded
from adoption until independent R/SAS verification and separate acceptance.

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
and exact-unit failure dependencies from the baseline specification. The twelve
hand references are now traceable below; executed clinical checks and selected
standards mappings remain pending.

[structure-only.recipe.json](../examples/clinical-review/structure-only.recipe.json)
is a runnable **generic** three-table structural example. Its clinical-looking
names and literal `baseline` text do not select clinical code. It is not a
clinical template and does not exercise derivations. The separate JSON review
sheets are deliberately rejected by the application recipe loader.

The range/scale, exact representation, overflow, six-place export and exact
primary comparison rules are adopted as `clinical-numeric/1` (E85). The six added
hand transcriptions are accepted (E83); the proposed adapter/interface boundary
and source implementation remain separate reviews. Independent comparison and
secondary tolerance verification remain pending in progress.json. This step
does not implement clinical calculations or authorize their implementation.

## Internal source contract

The bounded foundation uses `ravel-clinical-source/1` through an explicit
internal API in `ravel.clinical.source`. It is not a generation recipe or a
clinical template request. The public recipe loader continues to reject it.
No UI entry, arithmetic, dose selection, time comparison or clinical-policy
validator is introduced. The adopted numeric core above remains unimplemented.

The document contains ordered `subjects`, `treatments`, `parameters`, `pairs`
and `records` lists and a root `provenance` object. Subjects have `id` and
`treatment`; treatments/parameters have `id` and `unit`. Each explicit pair
contains `subject` and `parameter`, with no Cartesian expansion. These rows
also carry provenance. IDs are opaque nonempty strings; IDs are unique within
each declaration collection and across all source records. A pair's identity
is its two references. Empty record collections and unequal per-subject
counts are allowed.

A source record has `id`, `kind`, `subject`, `timestamp`, `value`, `unit`
and `provenance`. A `measurement` additionally has `parameter`; an
`exposure` has `treatment` and `status`. Status is supplied explicitly:
the review adapter maps the original `actual-dose`, `planned-dose` or
`not-administered` kind to that exposure status. Unknown statuses and
unparseable timestamp strings stay available for later clinical checks.
This structural validator does not interpret them or compare units.

Each provenance object requires nonempty `source` and `pointer` strings.
The explicit review adapter records the original file and JSON pointer for
each declaration, pair and source record. It retains source record ordering
and does not copy expected derived rows into the source contract. A supplied
contract can reference another explicitly named source without using that
review adapter.

`loads` parses JSON without binary floating-point conversion: integer and
fraction/exponent tokens become immutable `NumberToken` objects containing
their original spelling. `null`, strings and Booleans remain different.
Duplicate JSON keys and non-JSON NaN/Infinity tokens fail parsing. Parsing is
separate from `validate`, so a parsed malformed value is still inspectable.
`validate` requires the value field and permits a number token or explicit
null; text/Boolean/container values produce structural type diagnostics.
No scale, range, normalization, positivity, formatting or arithmetic policy is
selected. The shared 1 MiB input limit is a resource bound.

`dumps` followed by `loads` preserves the parsed document semantically,
including exact number-token spelling, timestamps, IDs, provenance and list
order. Whitespace and string-escape spelling are not preserved byte for byte.
Native Python floats/integers must not be substituted for source number
tokens. The original input file remains the byte-level authority.

`validate` returns a report explicitly scoped to `source_structure`, with
`passed`/`failed`, ordered `failures`, separate `not_evaluated` entries,
and `clinical_policy: not_evaluated`. Failures use the accepted code,
scope and source-ID conventions, with a check name and path. Ordering follows
declarations, subjects, pairs, then source records, in supplied order;
field checks use the contract's fixed order, not object-key order.
Unknown subject/parameter references are generic structural failures and
suppress only dependent pair-membership checks. Known references to an
undeclared pair yield `UNDECLARED_GROUP`, never a new group.

The reference sheets remain hand expectations. Illustrations a–c pass source
structure while their unit/tie/timestamp policy expectations remain unexecuted.
The crossed pair fails the now implemented membership check. No structural
success is a claim of clinical validation, derivation or R/SAS comparison.

### Source robustness follow-up

The 14 November batch reproduces round-trip failures at the exact 1 MiB
boundary, with large non-ASCII strings and with parser-supported nesting.
Serialization now uses an iterative compact encoder, retaining original number
tokens and escaping unpaired surrogates without expanding ordinary UTF-8 text.
It adds no trailing byte that would make an accepted maximum-size input fail
reload. Cyclic/native non-JSON objects fail with TypeError.

Duplicate declaration IDs make the corresponding reference ambiguous. An
unavailable identity collection or ambiguous referenced identity produces a
separate NOT_EVALUATED reference check, then suppresses dependent membership
conclusions. Independent field checks continue. Malformed review-sheet shapes
and unexpected record fields fail through ValidationError before mapping;
the adapter cannot silently replace supplied provenance.

The 15 November adapter follow-up rejects container-valued review record fields
with a source-located ValidationError before recursively copying any records.
A loader-supported value containing 700 nested arrays previously raised an
uncontrolled RecursionError in the adapter. Record fields in this review format
are scalar; no new numeric restriction or nesting limit is applied to the source
loader. Numeric tokens, explicit nulls and other scalar values remain available
for structural validation, with supplied ordering and adapter provenance intact.

No fixed nesting cap is adopted: the pinned JSON parser's supported inputs must
round-trip, and parser failures remain SourceParseError. A portable explicit
depth budget is a future resource-policy decision, not a clinical rule.

The bounded 15 November technical review also treats a skipped declaration
reference as an unavailable prerequisite for the pair collection. Measurements
then report pair membership as NOT_EVALUATED with `pair_declarations`, rather
than claiming UNDECLARED_GROUP from a partially evaluated declaration set.
Independent field failures remain evaluable. Diagnostic scopes follow the
accepted baseline specification: exposures use a known subject, measurements
need both known/unambiguous subject and parameter; otherwise retain record or
recipe scope. An unsupported parameter field cannot turn an exposure diagnostic
into a measurement-pair diagnostic. These are structural diagnostic repairs,
not numeric, timestamp, unit or clinical-status validation.

## Twelve-scenario reference coverage

[scenario-coverage.json](../examples/clinical-review/scenario-coverage.json)
maps all twelve plan requirements to explicit hand references. Existing C1–C4
and negative illustrations a/b are reused unchanged. Six additional supplied
source cases are in
[additional-scenarios.json](../examples/clinical-review/additional-scenarios.json);
Maksim accepted these six hand references on 15 November 2026 (E83),
as supplied at candidate 1335be1; their records and expected results are unchanged.
This accepts the references, not the source implementation or clinical execution.
Numeric-core adoption is recorded separately in E85. Labels are retained as source provenance; output rows are compared
by explicit IDs without adopting a new row-sort policy.

| Requirement | Reference |
| --- | --- |
| Ordinary baseline | C1 |
| Multiple eligible measurements | multiple-eligible |
| Latest pre-dose value missing | C2 |
| No eligible baseline | C3 |
| Exactly at dose | C4; C3 preserves the no-earlier-value companion |
| Post-dose labelled baseline | labelled-followup |
| Duplicate eligible timestamps | negative b |
| Out-of-order input | out-of-order |
| Missing actual dose | undosed, transcribed from the accepted auxiliary illustration |
| Incompatible units | negative a |
| No usable measurements | empty-measurements, the accepted empty-group illustration |
| Multiple subjects/parameters | grouping: three explicit pairs, no fourth Cartesian group |

Each requirement identifies classification, explanation, executable source/
reference checks and future clinical checks. Cases carry selected source IDs,
expected groups/changes/reasons/diagnostics; intentionally invalid cases retain
zero successful outputs and the separate NOT_EVALUATED expectations.
`python scripts/check_clinical_scenarios.py` checks coverage, source structure,
round trip and reference membership. It performs no timestamp ordering,
baseline selection, arithmetic or independent R/SAS derivation. R1 remains
incomplete until the actual clinical implementation and independent comparisons.
