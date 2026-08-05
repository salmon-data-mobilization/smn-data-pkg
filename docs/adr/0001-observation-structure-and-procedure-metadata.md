# ADR 0001: Measure-specific structures and SOSA procedures

- Status: accepted
- Date: 2026-08-04
- Applies to: backwards-compatible SDP 0.2 extension

## Context

Some salmon tables are physically wide but semantically mixed-grain. A stock-
recruit table may repeat a brood-year spawner estimate on several age-specific
recruit rows. Table-level primary keys cannot say which subset of columns
identifies each measure. SDP also carried a legacy `method_iri` beside I-ADOPT
fields, while older guides could be read as treating Method as an I-ADOPT
component. I-ADOPT defines no such component.

## Decision

Add two optional, paired CSV resources under `metadata/structure/`:

- `observation_structures.csv` declares one logical structure per measure.
- `observation_components.csv` binds columns as measure, dimension, or attribute.

Dimensions define the measure's grain. Each structure has exactly one measure
and at least one dimension, and repeated rows at the same declared dimension tuple must have invariant
measure and bound attribute values. The role names align with W3C RDF Data Cube,
but SDP does not assert that these CSVs are a Data Cube Data Structure
Definition. Exporters normalize each structure before choosing a Data Cube
representation.

The extension is optional as a pair, but complete when present: every
measurement column in the package is the measure of exactly one structure.
Grain and invariance comparisons use values normalized by the dictionary
`value_type`, so equivalent numeric lexical forms do not create false conflicts.

Add optional `metadata/methods.csv` as a registry of SOSA Procedure resources.
Retain `column_dictionary.method_iri` for compatibility, with clarified static
procedure semantics. Require the method registry when that static link is used
with the observation-structure extension, while preserving legacy packages
without either new extension. Represent a row-varying procedure as a categorical
attribute bound using `sosa:usedProcedure`. Do not model Method as an I-ADOPT
component. Every allowed code enumerated for that attribute resolves to a
registered method, whether or not the current data happen to use the code.

Standardize an optional top-level `reproducibility/` sidecar directory containing
`reviewed_semantic_selections.csv`, `workflow/`, `provenance/`, and `source/`.
These files preserve how a package was produced but do not change its observation
semantics.

## Consequences

- Existing SDP 0.2 packages remain valid without the new optional resources.
- Mixed-grain packages can declare safe measure-level projection and validation.
- Consumers can distinguish fixed variable context, row-varying dimensions,
  observation procedures, and transformation workflow.
- A future RDF exporter has an explicit normalization boundary; it must not treat
  this extension as direct Data Cube conformance.
- The v0.2 extension deliberately supports one structure per measurement column.
  More complex views or one measure in multiple structures require a future
  versioned decision.

## Alternatives considered

- Treat the table primary key as every measure's grain: rejected because it hides
  repeated coarser-grain observations.
- Put dimension bindings in compound variable terms: rejected because row-varying
  coordinates and fixed term semantics are different concerns.
- Use `qb:measureDimension` directly: rejected because that term describes Data
  Cube's long-form measure-type pattern, not per-measure dimension sets in a wide
  table.
- Add Method to I-ADOPT decomposition: rejected because the standard has no Method
  role; SOSA already models procedures associated with observations.
