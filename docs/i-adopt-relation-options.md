# I-ADOPT relation expressivity: decision proposal (B-154)

**Status:** proposal for Brett; no SDP rule or implementation is adopted by this
document. **Decision requested:** should a future SDP profile carry explicit
variable-to-entity and constraint-to-component relations, or deliberately leave
them outside the format? B-154 remains open until a ruling and both package
implementations satisfy its retirement condition.

## Evidence and boundary

The [I-ADOPT 1.1.0 ontology](https://i-adopt.github.io/ontology/) (release
2025-05-28) assigns different meanings to `hasObjectOfInterest`,
`hasContextObject`, and `hasMatrix`. `hasMatrix` is a subproperty of
`hasContextObject`; its use need not duplicate the latter edge.
`constrains` runs from a
Constraint to an Entity, Property, or StatisticalModifier. These are existing
ontology predicates, so the two gaps below concern **SDP representation**, not
missing ontology terms. Neither belongs in the ontology term-request pipeline.

The current [column dictionary schema](../schema/frictionless/metadata/column_dictionary.schema.json)
has one `entity_iri` (described as what a measurement is about) and an optional,
semicolon-separated `constraint_iri`. Neither field stores a predicate or a
constraint target. [The specification](../SPECIFICATION.md#measurement-column-requirements)
distinguishes a fixed variable constraint from a row-varying observation
dimension. `component_relation_iri` in the
[observation component schema](../schema/frictionless/metadata/observation_components.schema.json)
links an **observation** to one data column component; it is not an I-ADOPT
relation between components of a **variable**.

Both `metasalmon` and `metasalmonpy` currently write a 16-column,
manifest-bound `metadata/semantic/measurement-decompositions.csv` with repeated
`entity` and `constraint` components. This artifact is **not yet normative SDP**.
Its `component_relation` and `related_component_order` express only
`value_of_dimension` between two matched constraints. Reusing that value for
`constrains`, or treating every `entity` component as an ObjectOfInterest,
would erase the distinction the I-ADOPT predicates make. The existing
decomposition writer also matches each nonempty dictionary semantic slot to a
component of the same role; it does not give additional same-role components a
relation to the variable.

The two implementation references are `metasalmon/R/measurement-decompositions.R`
(`.ms_sdp_decomposition_columns`, `.ms_sdp_decomposition_validate_relations()`,
and `.ms_sdp_decomposition_validate_dictionary()`) and
`metasalmonpy/measurement_decompositions.py` (`_COLUMNS`,
`_validate_relations()`, and dictionary binding validation).

## Option A — an additive relation artifact (recommended for design)

**Candidate shape, not a released schema:** after B-114 admits the existing
decomposition artifact into the SDP specification, define one optional
`metadata/semantic/measurement-relations.csv` bound to those decomposition
rows. Keep all 16 existing decomposition columns and their `value_of_dimension`
meaning. A separate relation table avoids changing their byte-level contract.
Its candidate columns are:

| Column | Proposed meaning |
| --- | --- |
| `dataset_id`, `table_id`, `column_name`, `measurement_concept_iri` | The same four-field measurement binding as the decomposition table. |
| `subject_component_order` | Blank for the variable itself; otherwise an existing component order in that measurement. |
| `predicate_iri` | One of the four I-ADOPT predicates named below, using its full IRI. |
| `object_component_order` | An existing component order in that same measurement. |

The four predicate IRIs are
`https://w3id.org/iadopt/ont/hasObjectOfInterest`,
`https://w3id.org/iadopt/ont/hasContextObject`,
`https://w3id.org/iadopt/ont/hasMatrix`, and
`https://w3id.org/iadopt/ont/constrains`. For the first three, the subject is
the variable (blank order) and the object is a matched `entity` component. For
`constrains`, the subject is a matched `constraint` component and the object is
a matched `entity`, `property`, or `statistical_modifier` component. No `unit`
or observation-structure component can be the target of `constrains`.
The blank subject is a package-local reference to the variable description;
it does not assert that the dictionary's compound `term_iri` is an instance
of the I-ADOPT `Variable` class.

For example, within one measurement, component 2 can be the dictionary's
object-of-interest entity, component 3 a context entity, component 4 a matrix
entity, and component 5 a constraint. Rows `(blank, hasObjectOfInterest, 2)`,
`(blank, hasContextObject, 3)`, `(blank, hasMatrix, 4)`, and
`(5, constrains, 2)` preserve their distinct relations without inventing a
predicate or an ontology term. The source may include only the relations it
can justify; the reader must not infer a missing relation from list order,
component role, or a label. In particular, a matrix relation implies the
context-object relation by the ontology's subproperty axiom, so an exporter
need not write a redundant explicit context edge to the same component.

Adoption would need an exact normative choice for absent files and dictionary
projection. A safe candidate is: packages without the relation artifact remain
valid under their existing profile; when the artifact is present, exactly one
explicit `hasObjectOfInterest` row must target the matched entity component carrying
the dictionary's `entity_iri`. The relation table must have unique rows,
same-measurement references, valid role/status pairs, and an integrity binding
analogous to the decomposition manifest. A validator must reject a reference
to a missing component or wrong role; an RDF exporter must not silently fill
in a relation that the table did not state. These checks are part of a future
specification, not active rules today.

This option retains the existing dictionary and decomposition row formats,
allows multiple relations and multiple constraints, and gives consumers a
machine-readable target. Its cost is a third semantic artifact plus versioned
schema/manifest, validation, and mirror work. It is a **bounded I-ADOPT subset**,
not a claim that all I-ADOPT 1.1 graph patterns are supported.

## Option B — explicit refusal with consumer guidance

A ruling could instead say that SDP records only its current dictionary slots
and ordered decomposition components, with no normative way to distinguish
context object from matrix or to identify what a constraint constrains. The
specification would then say plainly:

- `entity_iri` supplies one entity for the measurement; other entity
  components are not assigned an I-ADOPT relation by the SDP.
- `constraint_iri` lists constraint terms without their targets.
- An exporter that needs these edges must obtain an independently authored
  I-ADOPT RDF description or another source with explicit provenance. It must
  not infer the edges from column labels, row order, `entity` role, or
  `value_of_dimension`. If the consumer requires lossless I-ADOPT output and
  lacks that source, it must report the missing relations instead of claiming
  a complete graph.

This keeps the SDP small and backwards compatible but leaves these two
distinctions unavailable to ordinary SDP consumers. It is a deliberate
capability limit, not a claim that the ontology lacks the predicates. The
same guidance would need to appear in R and Python read/write/export docs.

## Recommendation and adoption sequence

**Recommend Option A as the design target**, conditional on B-114. The
source ontology already specifies the relations, and the current decomposition
rows supply stable component identities to link. An additive table retains
the frozen rows and can be absent for existing packages. The proposal does
not choose a profile version, release date, default RDF projection, or final
schema; those are specification decisions for Brett after B-114's layout is
adopted. If a concrete consumer requirement or maintenance cost weighs
against the extra artifact, Option B states an implementable refusal.

B-114 is currently `needs_brett`: it requires the spec repository to adopt
`metadata/semantic/` and its manifest-bound decomposition layout before the
packages validate it as normative SDP. B-154 cannot quietly make that layout
normative through a guide. A later implementation should proceed in this order:

1. Resolve B-114's adoption and versioned profile/schema ownership.
2. Record Brett's B-154 choice and, for Option A, define the relation table,
   manifest, exact absent-file behavior, and validator rules in this repository.
3. Update **both** metasalmon and metasalmonpy readers, writers, validators,
   documentation, and parity records in the same stream; preserve their
   existing decomposition role vocabulary, CSV columns, and
   `value_of_dimension` semantics unless a separately reviewed migration is
   required.
4. Use shared fixtures to test a context object, a matrix, and constraints
   aimed separately at an entity, property, and statistical modifier; negative
   cases must include missing/wrong-role/cross-measurement targets, an
   unsupported predicate, and an absent relation artifact. Pin deterministic
   bytes and manifest hashes across R and Python. Test that neither reader
   silently maps an unqualified entity/constraint component to a relation.

The expected implementation surfaces, if Option A is chosen, are
`SPECIFICATION.md`, a new semantic metadata schema, a new versioned profile,
`schema/sdp.rules.yaml`, `scripts/validate_package.py`, and the generated
`docs/field-reference.md` here. In metasalmon they are
`R/measurement-decompositions.R` (new relation reader/writer alongside it),
`R/package-helpers.R` (optional-artifact validation), `R/knb-publication.R`
and `R/knb-sdp-archive.R` (publish only validated, declared bytes), with
contract checks in `tests/testthat/test-measurement-decompositions.R`,
`test-package-helpers.R`, `test-knb-publication.R`, and
`test-knb-sdp-archive.R`. The Python equivalents are
`measurement_decompositions.py` (or a neighboring relation module),
`package_io.py`, `knb_publication.py`, and `knb_archive.py`, with checks in
`tests/test_measurement_decompositions.py`, `test_validation_hardening.py`,
and `test_knb_publication.py`. This inventory names the integration points;
it does not direct a change to their current contracts in this proposal PR.

**Question for Brett:** adopt an explicit relation artifact after B-114, or
record the refusal and consumer guidance in Option B?
