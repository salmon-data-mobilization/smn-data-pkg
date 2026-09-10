# Changelog

All notable changes to the Salmon Data Package (SDP) specification will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed
- Descriptor `schema.fields` entries may carry the column dictionary's
  semantic annotation keys — `unit_iri`, `term_iri`, `term_type`,
  `property_iri`, `entity_iri`, `constraint_iri`,
  `statistical_modifier_iri` — beside the core `name`/`title`/`description`/
  `type`/`constraints` projection, named as the dictionary column with the
  dictionary value unchanged (hub backlog #90, ruled 2026-08-24: permit the
  keys). Both metasalmon and metasalmonpy project them, and
  `scripts/validate_package.py` compared the whole entry with `!=`, so every
  semantically annotated package failed strict publication validation while
  the only fixture under test carried no IRIs. The permitted keys are now
  derived from `column_dictionary.schema.json` — every dictionary column the
  core projection does not already express — rather than from a hand-written
  list, so a column added to the dictionary is permitted without editing the
  script. An unknown key is still rejected, a carried value must equal the
  CSV cell, and the core keys keep their exact comparison; the per-entry
  errors now name the key that differs. `SPECIFICATION.md` states the rule
  under "Data resource field entries".

### Fixed
- The four `ObservationStructureValidationTests` that still asserted the
  pre-0.3.0 method registry (`metadata/methods.csv`, dictionary `method_iri`)
  now assert the sdp-0.3.0 shape: enumerated procedure codes need absolute
  shared-vocabulary term IRIs, the static method reference is
  `tables.csv method_iri`, the dictionary rejects a `method_iri` column, and
  the descriptor must list the structure pair when present. The suite is
  green again (23/23); the validator itself was already correct.
- The generated template README no longer instructs deleting a
  `metadata/methods.csv` the template does not contain, and
  `generate_artifacts.py` now fails (`--write` and `--check`) when the README
  source names a `metadata/*.csv` absent from the generated template — the
  previous check copied the README verbatim and could not see stale prose.
- Dead documentation references removed or repointed: `docs/quickstart.md`
  (README, SPECIFICATION, entrypoints → README "Quick Start"),
  `docs/implementation-guide.md` (SPECIFICATION, entrypoints → `AGENTS.md`),
  `docs/edh-hnap-mapping.md` (README, SPECIFICATION → removed),
  `docs/sdp-profile-schema-guide.md` (SPECIFICATION → removed), and
  `schema/frictionless/metadata/methods.schema.json` (entrypoints → the
  sdp-0.3.0 method placement in `tables.schema.json`/`codes.schema.json`).
  Stale v0.2 profile pointers in README and entrypoints now point at the
  current v0.3 profile, with v0.2 marked as a frozen published contract.
- Both shipped examples now declare `spec_version`/`specVersion` `sdp-0.3.0`
  (they declared `sdp-0.2.0` at the sdp-0.3.0 tag and nothing noticed,
  because no tool reads the field); the dataset schema's `spec_version`
  example string moved with them.

### Added
- Minimal GitHub Actions CI (`.github/workflows/ci.yml`): the unit tests and
  `generate_artifacts.py --check` run on every push to `main` and every pull
  request. No release automation.

## [sdp-0.3.0] - 2026-08-14

### Changed (breaking)
- **Methods leave the column dictionary**: `column_dictionary.method_iri` is
  removed. A method describes how an observation was made, not what was
  observed; it is recorded at the coarsest level where it is still true —
  `tables.csv` `protocol_iri`/`protocol_citation` (primary; in-package
  protocols cite the package `README.md`), `tables.csv` `method_iri` (single
  method, no protocol document), or a data column bound with
  `sosa:usedProcedure` (row-varying). Migration guidance is in
  SPECIFICATION.md ("Migration from sdp-0.2.0").
- **The `metadata/methods.csv` registry is removed** (it was added in the
  observation-structures work and never released with a dated entry): methods
  are shared concepts with resolvable IRIs — labels and definitions belong to
  the vocabulary, version and citation to the protocol. `codes.csv` term IRIs
  for row-varying procedures resolve directly to shared-vocabulary
  `sosa:Procedure` concepts.

### Added
- `column_dictionary.statistical_modifier_iri`: the fifth I-ADOPT component
  column (`iop:StatisticalModifier`) stating what a reported value represents
  across the observations it summarizes; recommended vocabulary
  `smn:StatisticalModifierScheme` (smn 0.0.3).
- `tables.csv` `protocol_iri`, `protocol_citation`, `method_iri`;
  `dataset.csv` `protocol_iri`, `protocol_citation` (convenience).
- Rules: `methods_are_sosa_procedures` rewritten to the three placements;
  new `statistical_modifier_is_variable_identity`.

### Fixed
- The sdp-0.2.0 body of work (Frictionless-first schemas, v0.2 profile,
  `sdp.rules.yaml`, canonical layout) had no dated changelog entry; recorded
  here retroactively as released 2026-08-11 with the metasalmon 0.2.0
  re-vendor.

### Added

- Optional `metadata/methods.csv` registry for SOSA Procedure resources, with fixed procedures associated through the compatibility `column_dictionary.method_iri` field and row-varying procedures associated through `sosa:usedProcedure` observation attributes.
- Optional paired `metadata/structure/observation_structures.csv` and `observation_components.csv` resources for measure-specific dimension bindings and mixed-grain validation.
- Optional extended `reproducibility/` sidecar layout containing `reviewed_semantic_selections.csv`, `workflow/`, `provenance/`, and `source/`.
- Mixed-grain example, strict validation checks, Data Cube alignment guide, corrected I-ADOPT/SOSA guide, and architecture decision record.
- Dataset-level metadata fields to support EDH/GeoNetwork export when not derivable from data: `contact_org`, `contact_position`, `update_frequency`, `topic_categories`, `keywords`, and `security_classification`.
- Non-normative exporter guide `docs/edh-hnap-mapping.md` with an SDP `dataset.csv` → HNAP XML mapping table, including compact value-mapping dictionaries for `update_frequency` and `security_classification`.
- New `docs/quickstart.md` exporter-first quickstart clarifying SDP as an export-time metadata contract (no source database schema changes required).
- Authoritative Frictionless Table Schema files under `schema/frictionless/metadata/`.
- SDP Frictionless package profile at `profiles/salmon-data-package/v0.2/profile.json`.
- Custom SDP validation rules at `schema/sdp.rules.yaml` for cross-table/domain rules that Table Schema cannot express.
- Generated blank package template at `templates/salmon-data-package-template/` and `templates/salmon-data-package-template.zip`.
- Generated field reference at `docs/field-reference.md`.

### Changed

- Moved canonical SDP profile, rules, and metadata-schema URLs to the active
  `salmon-data-mobilization.github.io/smn-data-pkg` GitHub Pages site. The
  previously documented `dfo-pacific-science.github.io` URLs did not resolve.
- Observation-structure validation now requires complete measurement coverage and at least one dimension per structure when the optional extension is present, resolves its static and enumerated procedure references to the required method registry while retaining extension-free legacy packages, and compares grain/invariance using dictionary-typed values.
- Corrected example organism-count units to QUDT `INDIV` and use the shared Salmon Domain Ontology `Abundance` characteristic instead of nonexistent QUDT terms.
- Canonical SDP package layout is now explicitly documented as `metadata/*.csv` + `data/*.csv`; complete/published packages require generated root `datapackage.json` declaring the SDP Frictionless profile.
- Updated `SPECIFICATION.md`, `docs/quickstart.md`, and `examples/minimal-example/` to align with the same canonical folder layout used by `metasalmon`.
- Harmonized `dataset.csv` field semantics to reduce overlap: clarified distinction among `creator`, `contact_name`, `contact_org`, `contact_position`, `topic_categories`, and `keywords`.
- Replaced hand-maintained `schemas/*.csv` schema summaries and the custom YAML field registry with Frictionless-first schema artifacts.

## [0.1.1] - 2026-2026-01-14

### Added

- SDP semantic columns (`property_iri`, `entity_iri`, `constraint_iri`, and the separate SOSA-aligned `method_iri`) in `column_dictionary.csv` (the compound variable remains in `term_iri`, and units stay in `unit_iri`). This historical entry is clarified because Method is not an I-ADOPT component.
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
