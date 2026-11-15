# Bounded linked generic tables

Issue #15 contract and invented reference fixed before implementation on
18 October 2026. `ravel-dataset/1` is a separate explicit dataset format; existing
single-table formats preserve their outputs. No clinical interpretation is
activated by names. This first increment does not fit joined samples.

The recipe has `format`, one global `seed`, ordered `tables` and `relationships`.
There are 1–8 tables, each with stable `id`, display `name`, `row_count`, ordered
`fields` and a `primary_key` field identity (or null for an unrelated table).
Fields use the version3 scalar rules. A relationship has stable `id`, `parent`,
`parent_key`, `child`, `foreign_key` field identity and `children_per_parent`.
It references the parent's declared primary key. A child has at most one parent;
the graph must be acyclic. Compound keys, arbitrary joins and cycles are rejected.

`foreign_key` and `child_index` are structural field kinds with zero missingness
and no scalar parameters. Every foreign-key field belongs to exactly one
relationship; child-index fields require a parent relationship. Child rows are
ordered by parent output order, then index1…children_per_parent. Parent keys
repeat in that order. Other child fields use their own stable table/field streams.

Counts are explicit: the child's declared row count must equal parent row count
times children_per_parent. Changing a count cannot silently rewrite another table.
Each table stays within 100,000 rows/50 fields, and the complete dataset within
two million cells. Relationship counts are positive integers; total tables and
links remain bounded. Unsupported references, mismatched counts, orphan fields,
cycles, missing/duplicate keys and infeasible scalar rules fail before successful
output. IDs and declared finite-domain unique fields provide supported primary
keys; a constant key is permitted only for a singleton table. All generated keys
and foreign keys are checked again before constructing the successful result.

The UI selects a table while keeping one global recipe/result freshness state.
Fields, per-table rows and actual previews share the existing workbench. A compact
relationship editor explicitly sets its parent, key and children-per-parent;
its displayed resulting total is applied only with confirmation. Drafts block
table switching. Table additions preserve existing table/field identities.
Only the runnable Devices/measurements example appears under Use template.

CLI directory export stages the complete set before a final directory rename:
one `<stable_table_id>.csv` per table, `recipe.json`, `dictionary.json`, `run.json`.
Existing destinations/files are never overwritten. Ordinary failed writes remove
only their own temporary staging directory and expose no successful partial set.
This is not a power-loss transaction or a cross-filesystem operation. UI dataset
export is one complete ZIP with the same files; selected-table CSV remains
available. Recipe, dictionary and validation/run record describe the full dataset.

## Reference established by hand

Three devices have keys D01,D02,D03. Exactly two measurements per device yield
six measurements with unique M01…M06 keys and these key/slot pairs:

| Measurement | Device | Slot |
| --- | --- | ---: |
| M01 | D01 | 1 |
| M02 | D01 | 2 |
| M03 | D02 | 1 |
| M04 | D02 | 2 |
| M05 | D03 | 1 |
| M06 | D03 | 2 |

These are structural expectations, not generator output. Reject a relationship
referencing a missing parent key/foreign-key field, a three-row constant primary
key, declared child count5 instead of6, and a devices↔measurements cycle. Adding
an independent field leaves all prior table values unchanged. Save/reload, all
CSV files, dictionary/run metadata and UI/CLI agreement must be checked.

No clinical baseline derivation, joined-sample fitting, public extension API or
release acceptance is implied. Actual checks belong in progress.json.
