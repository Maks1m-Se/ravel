# Recipe outline and ownership boundary

M0-04 architectural outline accepted after Hub review of `eb809e1`: one shared
recipe, explicit domain routing, ownership boundaries, separate schema versioning,
and stable entity/field random streams. Field names and rule notation below remain
illustrative, not a stable schema or an implemented generator contract. Scope
and release criteria remain in [the plan](plan.md).

## One saved recipe

Use one JSON-compatible recipe shared by the CLI and future Guided and
Advanced interfaces. All views edit the same settings; switching views or
saving/reloading must preserve them. Recipes contain declarative data, not
executable Python, SQL, or expressions.

| Part | Proposed purpose |
| --- | --- |
| `schema_version` | Recipe format version, separate from application version; `1` below is illustrative |
| `seed` | Explicit random seed; reproducibility also requires the recorded application and environment versions |
| `domain` | Explicit generic mode or clinical mode with a named template and compatible template version; exact field naming remains illustrative |
| `entities` | Named record collections, requested counts, typed fields, and keys |
| `relationships` | Parent/child links, foreign keys, and explicit child counts per parent |
| `generation_rules` | Named operations with explicit parameters, including constants, sequences, and supported distributions |
| `constraints` | Required counts, uniqueness, nonmissing values, referential integrity, ranges, quotas, and supported temporal relations |

Record application, dependency environment, schema, and domain-module versions
with each run as required by the plan. An unsupported schema version must fail
clearly before generation, identifying the supplied version and supported
versions. Any migration produces a separately saved, reviewable copy and
preserves the original. Acceptance of this outline does not establish schema stability.

Domain selection is explicit. Generic mode activates only the stated generic
rules; clinical-looking entity or field names must not activate clinical rules.
A future clinical recipe must explicitly select clinical mode, a named clinical
template, and a template version compatible with the bundled clinical module.
Unknown templates or incompatible versions must fail clearly rather than fall
back to inferred rules. Template selection does not settle the M0-05 clinical
decisions deferred below.

## Illustrative structural example

This is a generic structural example. All names and values are invented.
This JSON describes two subjects, one exposure record per subject, and two
biomarker measurements per subject. It
does not define dosing, visit timing, baseline, or change. No generator runs
this example today.

```json
{
  "schema_version": 1,
  "seed": 17,
  "domain": {"mode": "generic"},
  "entities": {
    "subjects": {
      "count": 2,
      "key": "subject_id",
      "fields": {"subject_id": "string"}
    },
    "exposures": {
      "count": 2,
      "key": "exposure_id",
      "fields": {"exposure_id": "string", "subject_id": "string"}
    },
    "measurements": {
      "count": 4,
      "key": "measurement_id",
      "fields": {
        "measurement_id": "string", "subject_id": "string",
        "slot": "integer", "parameter": "string", "value": "number", "unit": "string"
      }
    }
  },
  "relationships": [
    {"parent": "subjects.subject_id", "child": "exposures.subject_id", "children_per_parent": 1},
    {"parent": "subjects.subject_id", "child": "measurements.subject_id", "children_per_parent": 2}
  ],
  "generation_rules": [
    {"field": "subjects.subject_id", "operation": "sequence", "prefix": "S", "start": 1, "width": 2},
    {"field": "exposures.exposure_id", "operation": "sequence", "prefix": "E", "start": 1, "width": 2},
    {"field": "measurements.measurement_id", "operation": "sequence", "prefix": "B", "start": 1, "width": 2},
    {"field": "measurements.slot", "operation": "per_parent_values", "values": [1, 2]},
    {"field": "measurements.parameter", "operation": "constant", "value": "fictional-X"},
    {"field": "measurements.value", "operation": "per_parent_values", "values": [10, 12]},
    {"field": "measurements.unit", "operation": "constant", "value": "demo-unit"}
  ],
  "constraints": {
    "exact_counts": {"subjects": 2, "exposures": 2, "measurements": 4},
    "unique_entity_keys": true,
    "all_fields_required": true,
    "enforce_relationships": true
  }
}
```

For this illustration, sequences advance once per entity row in subject order
S01, S02; child slots are ordered within each parent. Relationships populate
the foreign keys by expanding each subject. `per_parent_values` assigns its
list in slot order for each parent. Counts must agree with that expansion;
they are assertions, not competing instructions. Slots are structural ordinals,
not visits. `fictional-X` and `demo-unit` are opaque illustrative labels with
no clinical interpretation or conversion rule.

Hand-checkable expected structure:

| Entity | Key | Subject link | Slot | Parameter | Value | Unit |
| --- | --- | --- | --- | --- | --- | --- |
| subjects | S01 | — | — | — | — | — |
| subjects | S02 | — | — | — | — | — |
| exposures | E01 | S01 | — | — | — | — |
| exposures | E02 | S02 | — | — | — | — |
| measurements | B01 | S01 | 1 | fictional-X | 10 | demo-unit |
| measurements | B02 | S01 | 2 | fictional-X | 12 | demo-unit |
| measurements | B03 | S02 | 1 | fictional-X | 10 | demo-unit |
| measurements | B04 | S02 | 2 | fictional-X | 12 | demo-unit |

Expected totals are 2 + 2 + 4 = 8 records. Each collection has unique keys;
every child references one existing subject. Each subject has exactly one
exposure and two measurements. These expectations were established directly
from the structural request, without executing generation or clinical derivation.

## Ownership boundary

| Owner | Responsibilities |
| --- | --- |
| General engine | Generic counts, typed fields, keys, relationship expansion, distributions, random streams, explicit constraints, recipe/input validation, and structural output validation; reject unsupported or infeasible requests clearly without silently relaxing rules or returning successful partial output |
| Bundled clinical module | Meaning of subjects, actual dose, visits, biomarker parameters and units, baseline/change, and clinical validation; translate explicit domain settings into engine requests and derive clinical outputs from underlying records |
| Thin CLI/UI/export adapters | Collect and display settings and errors, preserve the shared recipe, invoke validation/generation, and serialize datasets, recipes, dictionaries, and reports; do not infer clinical rules or duplicate generation/validation logic |

For [R3 reproducibility](plan.md), the general engine must derive stable random
streams from the seed and entity/field identities so adding an independent
field leaves existing fields unchanged in the same pinned environment.
Independent fields must not consume a shared stream whose draw order changes
when a field is added. The precise RNG algorithm and stream-derivation method
remain implementation choices to verify against R3; this outline selects neither.

The engine can handle a numeric field or a temporal constraint without knowing
that it represents a dose or a clinical visit. The clinical module owns why a
constraint applies and its clinical interpretation; the engine enforces its
supported generic form. Export adapters format outputs without changing values
or deriving baseline. The clinical module remains bundled in the same repository
and distribution. This task introduces no plugin framework, dependencies, or code.

## Explicit settings and editable assumptions

Directly entered settings populate the recipe. Later sample profiling may offer
editable estimates for the same fields, categories, missingness, and distribution
parameters. Show their source and proposed values, let users accept or override
them, and save the resulting explicit settings before generation. Record which
assumptions were sample-derived and which were overridden; the representation
of that provenance remains to be specified in M3.

Do not silently add dependencies, clinical rules, quotas, or new categories.
Identifier fields are excluded from fitting by default, and independent marginal
estimates must not imply preserved associations. Unsupported assumptions must
be reported. Both entry paths feed the same validation and engine; detailed
profiling and generated-only/retain-and-extend behaviour remain M3 work.

## Clinical proposal and deferred work

The existing baseline/change rule is in [the plan's Clinical specification
paragraph](plan.md), immediately before the twelve reference cases. It remains
the planning rule; this example neither extends nor validates it.

The separate [M0-05 baseline proposal](baseline-specification.md) records
actual-dose, eligibility, time, tie, unit and error policies with three
hand-worked cases. Those proposed policies and results await maintainer review;
they do not change this generic example or establish clinical validation.
Selected standards mappings and their exact
versions and limitations remain M2 work. Schema details and stability require
further specification and review; application, clinical, and release-gate validation have not occurred.
