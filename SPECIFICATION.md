# Salmon Data Package Specification

**Version**: sdp-0.2.0  
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
- One or more data files referenced from `metadata/tables.csv` (typically under `data/`).

For a complete published SDP:

- `datapackage.json` - a generated JSON (a text format for structured data) descriptor declaring the SDP Frictionless profile and listing the SDP metadata resources plus the data resources.

Optional sidecars:

- Additional sidecars such as `README.md`, `run-log.md`, `decision-log.md`, `qc-summary.md`, or `metadata_notes.md`.

Canonical directory layout:

```text
<package>/
  metadata/
    dataset.csv
    tables.csv
    column_dictionary.csv
    codes.csv        # omit when not needed
  data/
    <table files referenced from metadata/tables.csv>
  datapackage.json   # required for complete/published packages
```

Compatibility note:
- Strict SDP publication validation only validates the canonical `metadata/` + `data/` layout above.
- Older draft package shapes are outside this version's canonical package shape.

## `datapackage.json` guidance

The root `datapackage.json` is required for complete/published SDP packages. Blank authoring templates may omit it because tools should generate it from the filled CSV metadata and data files.

Minimum requirements:

- Set `profile` to `https://dfo-pacific-science.github.io/smn-data-pkg/profiles/salmon-data-package/v0.2/profile.json`.
- Include tabular resources for `metadata/dataset.csv`, `metadata/tables.csv`, `metadata/column_dictionary.csv`, and `metadata/codes.csv` when `codes.csv` is present.
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

Identifiers are `dataset_id`, `table_id`, and `column_name`.

- `dataset_id` is an opaque identifier used to join across metadata files. It must be unique within the package. Prefer a DOI (Digital Object Identifier, a persistent identifier for a dataset or publication) when available; otherwise use a stable local identifier.
- `table_id` and `column_name` are constrained for tool-friendly joins:
  - Allowed characters: letters, numbers, and underscore.
  - Start with a letter or underscore.
  - `table_id` must be unique within a `dataset_id`.
  - `column_name` must be unique within a `table_id`.

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

`constraint_iri` and `method_iri` are optional.

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
- `docs/sdp-profile-schema-guide.md`
- `docs/edh-hnap-mapping.md`
