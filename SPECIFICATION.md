# Salmon Data Package Specification

**Version**: sdp-0.3.0
**Author**: Brett Johnson, Data Stewardship Unit (DFO Pacific Region Science Branch)

## Scope

This specification defines the required files and CSV schemas (a schema is the list of columns and rules for a file) for a Salmon Data Package (SDP). SDP is a CSV-canonical custom Frictionless Data Package profile that uses Tabular Data Resource resources.

The authoritative machine-readable metadata schemas are the Frictionless Table Schema files in `schema/frictionless/metadata/`. The package profile is `profiles/salmon-data-package/v0.2/profile.json`. Salmon-specific cross-table and domain rules that are not expressible in Table Schema live in `schema/sdp.rules.yaml`.

This file does **not** designate project-specific canonical assessment locations; that is handled by each project repo. For SPSR, canonical assessment/mapping artifacts are managed in `Br-Johnson/smn-data-gpt/assessments/spsr`.

## Package layout

The **canonical** SDP package layout is:

- `metadata/dataset.csv` - dataset-level metadata.
- `metadata/tables.csv` - table-level metadata.
- `metadata/column_dictionary.csv` - column-level metadata.
- `metadata/codes.csv` - controlled code lists (a controlled vocabulary is a defined list of allowed values) when categorical columns exist.
- `metadata/structure/observation_structures.csv` and `metadata/structure/observation_components.csv` - optional paired files that declare measure-specific logical grain in wide or mixed-grain tables.
- One or more data files referenced from `metadata/tables.csv` (typically under `data/`).

For a complete published SDP:

- `datapackage.json` - a generated JSON (a text format for structured data) descriptor declaring the SDP Frictionless profile and listing the SDP metadata resources plus the data resources.

The directory is the canonical package shape. A ZIP may be created as a transport
serialization, but it is not a second dataset resource and need not be stored
inside or alongside a catalog record.

Optional reproducibility sidecars belong under `reproducibility/`, at the same
directory level as `data/` and `metadata/`:

- `reviewed_semantic_selections.csv` - a review ledger for semantic choices.
- `workflow/` - transformation code, notebooks, environment declarations, and run instructions.
- `provenance/` - transformation provenance and decision records.
- `source/` - redistributable source snapshots when they add lineage value and do not merely duplicate canonical `data/` files.

These sidecars document how an SDP was produced. They are not canonical SDP
semantic metadata and are not listed as Tabular Data Resources unless an export
profile explicitly requires that treatment.

Canonical directory layout:

```text
<package>/
  metadata/
    dataset.csv
    tables.csv
    column_dictionary.csv
    codes.csv        # omit when not needed
    structure/       # optional; both files are present together
      observation_structures.csv
      observation_components.csv
  data/
    <table files referenced from metadata/tables.csv>
  reproducibility/   # optional sidecars
    reviewed_semantic_selections.csv
    workflow/
    provenance/
    source/
  datapackage.json   # required for complete/published packages
```

Compatibility note:
- Strict SDP publication validation validates the core layout and any recognized optional metadata files that are present. Reproducibility sidecars are preserved but are outside SDP validity checks.
- Older draft package shapes are outside this version's canonical package shape.

## `datapackage.json` guidance

The root `datapackage.json` is required for complete/published SDP packages. Blank authoring templates may omit it because tools should generate it from the filled CSV metadata and data files.

Minimum requirements:

- Set `profile` to `https://salmon-data-mobilization.github.io/smn-data-pkg/profiles/salmon-data-package/v0.2/profile.json`.
- Include tabular resources for `metadata/dataset.csv`, `metadata/tables.csv`, `metadata/column_dictionary.csv`, and `metadata/codes.csv` when `codes.csv` is present.
- Include resources for the paired observation-structure files when those optional files are present.
- Reference the canonical Frictionless Table Schema URL for each SDP metadata resource.
- Include one data resource for each row in `metadata/tables.csv`.
- Set each resource path to the matching `file_name` value from `metadata/tables.csv`.
- Include a field entry for each matching row in `metadata/column_dictionary.csv`.
- Keep package title, description, license, resource paths, table labels, and field names consistent with the CSV metadata.

If a CSV value and the generated `datapackage.json` disagree, the package is invalid and must be regenerated or corrected.

## CSV format rules

- Files are CSV (a text file where each row is a line and columns are separated by commas).
- Encoding is UTF-8 (a standard text encoding).
- The first row is a header row with column names.
- Fields containing commas, quotes, or newlines must be wrapped in double quotes; embedded quotes are doubled.
- Line endings may be LF or CRLF.
- Canonical metadata CSV headers must exactly match their Frictionless Table Schema fields, in schema order, with no extra columns.
- Optional, recommended, and conditional fields are optional values, not optional headers. Leave allowed empty values blank.
- Required fields must be non-empty.
- Boolean fields use `TRUE` or `FALSE` (uppercase).
- Identifier matching is case-sensitive.

## Identifier rules

Identifiers are `dataset_id`, `table_id`, `column_name`, and
`observation_structure_id`.

- `dataset_id` is an opaque identifier used to join across metadata files. It must be unique within the package. Prefer a DOI (Digital Object Identifier, a persistent identifier for a dataset or publication) when available; otherwise use a stable local identifier.
- `table_id` and `column_name` are constrained for tool-friendly joins:
  - Allowed characters: letters, numbers, and underscore.
  - Start with a letter or underscore.
  - `table_id` must be unique within a `dataset_id`.
  - `column_name` must be unique within a `table_id`.
- `observation_structure_id` follows the same allowed-character rule and must be
  unique within its `dataset_id` and `table_id`.

## Data types

Value types used in `column_dictionary.csv`:

- `integer`: whole numbers only.
- `number`: numeric values with optional decimals.
- `string`: any text.
- `boolean`: `TRUE` or `FALSE` in metadata.
- `date`: ISO 8601 date (a standard date format) as `YYYY-MM-DD`.
- `datetime`: ISO 8601 datetime as `YYYY-MM-DDTHH:MM:SSZ` or with a timezone offset.

## Metadata field reference

The authoritative machine-readable metadata field names, order, types, requirements, examples, and conditions are defined in `schema/frictionless/metadata/*.schema.json`.

The generated human-readable field reference is `docs/field-reference.md`. Do not maintain duplicate field tables in this file.

`metadata/dataset.csv` temporal coverage fields, `temporal_start` and `temporal_end`, accept either a year (`YYYY`) or a full date (`YYYY-MM-DD`). Partial dates such as `YYYY-MM` are invalid.

## Measurement column requirements

A measurement column (a column whose values are the observed or computed quantity) must include:

- `unit_iri`
- `term_iri`
- `property_iri`
- `entity_iri`

`constraint_iri` is optional and may contain multiple semicolon-separated IRIs.

`statistical_modifier_iri` is optional and states what the reported value
represents across the observations it summarizes — mean, maximum, total, peak.
It resolves to an I-ADOPT `StatisticalModifier` concept (recommended
vocabulary: `smn:StatisticalModifierScheme`). A statistical modifier is part
of **variable identity**: daily mean and daily maximum temperature are
different variables. A method is never recorded here.

The column dictionary carries **no method field** (`method_iri` was removed
in sdp-0.3.0): a method describes how an observation was made, not what was
observed, which is also why I-ADOPT defines no Method component. Method
provenance is modelled separately using SOSA — see *Methods and procedures*.

## Measure-specific observation structures

The paired optional files under `metadata/structure/` describe logical
observations when one physical table contains measures at different grains.
They are unnecessary when table-level row semantics already describe every
measure without ambiguity.

- `observation_structures.csv` declares package-local structures within a table.
- `observation_components.csv` binds columns to `measure`, `dimension`, or
  `attribute` roles for each structure.
- Each structure has exactly one measure and at least one dimension. When the
  paired extension is present, every measurement column is the measure of
  exactly one structure.
- Dimensions identify a logical observation and therefore define that measure's
  grain. Attributes describe an observation without changing its grain.
- Component order is unique and contiguous from one. A column is bound at most
  once per structure.
- Measure and dimension components set `required_when_observed` to `TRUE`. When
  a measure value is non-empty, every component marked `TRUE` is non-empty.
- If a wide table repeats a coarser-grain observation across finer-grain rows,
  its measure and bound attributes must be invariant for a repeated dimension
  tuple after values are normalized according to their dictionary
  `value_type`.

The role names align conceptually with W3C RDF Data Cube component roles, but
these CSV files are not an RDF Data Cube Data Structure Definition and do not by
themselves assert Data Cube conformance. An exporter can project each SDP
structure into a normalized observation stream and an appropriate Data Cube
structure. Data Cube `qb:measureDimension`/`qb:measureType` is a specific
long-form multi-measure pattern; it is not a synonym for SDP's measure-specific
dimension binding.

An I-ADOPT `constraint_iri` and a structure dimension answer different questions.
A constraint is fixed semantic context in the variable definition; a dimension
is a row-varying coordinate that identifies a particular observation. A column
label alone is not machine-readable decomposition. If the compound `term_iri`
does not expose that fixed context to consumers, retain the appropriate
I-ADOPT constraint even when the label mentions it.

## Methods and procedures

**The one rule: a method describes how an observation was made, not what was
observed. Record it at the coarsest level where it is still true.** Recording
a method more finely than it actually varies is not more precise — it is
repetition that will drift out of sync.

The concept model is **Protocol > Method** (following
PNAMP/monitoringresources.org). A *protocol* is a documented plan someone else
could follow; it specifies which methods apply to which measurements, and it
is cited, not executed. A *method* is a technique named by a protocol and
applied to produce a value, with two subtypes rather than parallel concepts:
observation methods (how it was observed) and analytical methods (how the
number was derived). Every method or protocol IRI resolves to a shared
vocabulary concept typed as a `sosa:Procedure`; there is **no per-package
method registry** — labels and definitions belong to the vocabulary the IRI
resolves to, and version and citation belong to the protocol.

A protocol does not have to be external. Three forms, in descending order of
preference:

| Form | How it is referenced |
|---|---|
| **Published** — DOI or stable URL | `protocol_iri` points at it |
| **In-package** — described in the package's own `README.md` | `protocol_citation` names the section; `protocol_iri` may be omitted |
| **Undocumented** | Say nothing. An absent protocol is honest |

Placements, decided by one question — *is the method the same at this level?*
— asked coarsest-first:

| Level | Fields | Use when |
|---|---|---|
| **Table** (observation unit) | `tables.csv` `protocol_iri`, `protocol_citation` | **Start here.** A protocol governs a kind of observation event — a site visit — which is what a tidy table is |
| **Dataset** | `dataset.csv` `protocol_iri`, `protocol_citation` | Convenience only: the same protocol governs every table |
| **Table** | `tables.csv` `method_iri` | A single method applies and there is no protocol document to cite |
| **Row** | A data column bound with `sosa:usedProcedure` | The method varies from row to row — it is data, not metadata |

For row-varying procedures, bind a categorical column as an observation
`attribute` with `component_relation_iri` equal to
`http://www.w3.org/ns/sosa/usedProcedure`. Every enumerated code in that
column, including currently unobserved allowed values, has a `codes.csv`
`term_iri` resolving to a shared-vocabulary `sosa:Procedure` concept.

Transformation scripts, execution environments, parameter files, and detailed
run provenance belong under `reproducibility/`.

### Migration from sdp-0.2.0

A `method_iri` on a measurement column becomes the table's `method_iri` when
all measurement columns in the table agree. When they disagree, migration
**stops and reports** rather than guessing: the contributor decides whether to
split the table, cite a protocol, or move the method into the data. A
`REVIEW:`-marked value is dropped, not migrated. `metadata/methods.csv` is
removed; its labels and descriptions belong in the shared vocabulary, its
version and citation beside `protocol_iri`.

## Codes rules

- `code_value` is required unless `vocabulary_iri` is provided.
- A blank `code_value` with `vocabulary_iri` describes an external vocabulary reference; it does not enumerate observed values by itself.
- Every non-empty observed categorical data value must have exactly one matching `metadata/codes.csv` row with the same `code_value`.
- If `code_value` is present, providing `term_iri` is strongly recommended for machine-readable integration.
- Treat `codes.csv` as canonical (single source of truth) for code meaning (labels/descriptions) and optional code-level IRIs. In data files, prefer storing only the code value and join to `codes.csv` when you need labels/IRIs; avoid duplicating `*_label` / `*_iri` columns unless generating a derived export.
- If no categorical columns exist, `codes.csv` may be omitted.

## Versioning and extensions

- Project-specific metadata extensions belong in sidecar files or non-SDP descriptor fields. Strict publication validation rejects extra columns in canonical SDP metadata CSVs.
- Breaking changes to required columns or semantics should bump the major version.

## Non-normative guides

These documents provide guidance and implementation detail but do not change validity rules:

- `docs/quickstart.md`
- `docs/implementation-guide.md`
- `docs/i-adopt-integration-guide.md`
- `docs/observation-structure-guide.md`
- `docs/adr/0001-observation-structure-and-procedure-metadata.md`
- `docs/sdp-profile-schema-guide.md`
- `docs/edh-hnap-mapping.md`
