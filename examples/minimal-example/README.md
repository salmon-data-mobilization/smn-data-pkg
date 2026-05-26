# Minimal Example: NuSEDS Fraser-area Coho Sample

This is a minimal example of a Salmon Data Package (SDP) demonstrating the structure and metadata required for a valid SDP package.

## Package Contents

- `metadata/dataset.csv` - Dataset-level metadata
- `metadata/tables.csv` - Table metadata
- `metadata/column_dictionary.csv` - Column definitions with ontology links
- `metadata/codes.csv` - Controlled vocabulary codes (only when categorical columns exist)
- `data/nuseds-fraser-coho-sample.csv` - Minimal sample data table referenced from `metadata/tables.csv`
- `datapackage.json` - Generated package descriptor declaring the SDP Frictionless profile

## Dataset Description

This example package contains metadata for a sample of coho escapement records from PFMA 29 (Fraser River watershed) exported from NuSEDS (New Salmon Escapement Database System).

`metadata/dataset.csv` also demonstrates optional discovery/export fields (`contact_org`, `contact_position`, `update_frequency`, `topic_categories`, `keywords`, `security_classification`) that support downstream catalog export (for example EDH/GeoNetwork) without requiring source database schema changes.

This example shows the I-ADOPT-style component columns on one measurement column: `term_iri`, `property_iri`, `entity_iri`, and `unit_iri` are required for measurements; `constraint_iri` is optional; `method_iri` is an optional procedure/method link (aligned to SOSA `sosa:Procedure`, where SOSA is the W3C/OGC observations vocabulary). `term_iri` is the compound-variable pointer.

## Usage

This example can be used to:
- Understand the SDP structure
- Test SDP validation tools
- Serve as a template for creating new SDP packages

See the [quickstart](../../docs/quickstart.md) for a walkthrough and the [specification](../../SPECIFICATION.md) for rules on each metadata file.
