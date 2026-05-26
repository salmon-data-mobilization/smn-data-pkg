# Changelog

All notable changes to the Salmon Data Package (SDP) specification will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Dataset-level metadata fields to support EDH/GeoNetwork export when not derivable from data: `contact_org`, `contact_position`, `update_frequency`, `topic_categories`, `keywords`, and `security_classification`.
- Non-normative exporter guide `docs/edh-hnap-mapping.md` with an SDP `dataset.csv` → HNAP XML mapping table, including compact value-mapping dictionaries for `update_frequency` and `security_classification`.
- New `docs/quickstart.md` exporter-first quickstart clarifying SDP as an export-time metadata contract (no source database schema changes required).
- Authoritative Frictionless Table Schema files under `schema/frictionless/metadata/`.
- SDP Frictionless package profile at `profiles/salmon-data-package/v0.2/profile.json`.
- Custom SDP validation rules at `schema/sdp.rules.yaml` for cross-table/domain rules that Table Schema cannot express.
- Generated blank package template at `templates/salmon-data-package-template/` and `templates/salmon-data-package-template.zip`.
- Generated field reference at `docs/field-reference.md`.

### Changed

- Canonical SDP package layout is now explicitly documented as `metadata/*.csv` + `data/*.csv`; complete/published packages require generated root `datapackage.json` declaring the SDP Frictionless profile.
- Updated `SPECIFICATION.md`, `docs/quickstart.md`, and `examples/minimal-example/` to align with the same canonical folder layout used by `metasalmon`.
- Harmonized `dataset.csv` field semantics to reduce overlap: clarified distinction among `creator`, `contact_name`, `contact_org`, `contact_position`, `topic_categories`, and `keywords`.
- Replaced hand-maintained `schemas/*.csv` schema summaries and the custom YAML field registry with Frictionless-first schema artifacts.

## [0.1.1] - 2026-2026-01-14

### Added

- SDP I-ADOPT component columns (`property_iri`, `entity_iri`, `constraint_iri`, `method_iri`) in `column_dictionary.csv` (the compound variable remains in `term_iri`, and units stay in `unit_iri`).
- Documentation for measurement-required I-ADOPT components in `SPECIFICATION.md` and updated minimal example showing required measurement fields.
- ExecPlan for I-ADOPT adoption across SDP, ontology docs, and metasalmon tooling.
- Initial project structure
- Schema definitions in `schemas/` directory
- Specification document (SPECIFICATION.md)
- Minimal example package

### Changed

- Condensed `SPECIFICATION.md` to normative rules and added `docs/quickstart.md` and `docs/implementation-guide.md` for guidance.

## [0.1.0] - 2025-12-21

### Added

- Initial specification draft
- Core metadata schemas: `dataset.csv`, `tables.csv`, `column_dictionary.csv`, `codes.csv`
- Support for ontology linking via IRIs
- Support for SKOS concept schemes
- Column role classification system
- Frictionless Data Package compatibility and integration
- Comprehensive validation framework (structural, semantic, domain-specific)
- IRI field harmonization with "Recommended" category
- Clarified distinction between `observation_unit_iri` (table-level unit-of-observation) and `term_iri` (column-level variable), and aligned naming with SSN/OMS/OBOE mapping
