# I-ADOPT and procedure integration guide

SDP measurement semantics combine several standards with distinct jobs:

- `term_iri` identifies the compound variable term used for discovery or
  catalog export.
- `property_iri`, `entity_iri`, and `constraint_iri` record I-ADOPT variable
  components.
- `unit_iri` identifies the unit outside the I-ADOPT decomposition.
- method metadata records a SOSA Procedure association outside the I-ADOPT
  decomposition.

I-ADOPT 1.1 defines Variable, Property, Entity, Constraint, and Statistical
Modifier roles. It does **not** define a native Method or Procedure component.
Do not mint `iadopt:Method`, `iadopt:hasMethod`, or an SDP-specific predicate
that implies such a role.

SDP retains `column_dictionary.method_iri` for backwards compatibility. Its
normative meaning is a static `sosa:Procedure` association applying to all
non-empty measurements in that column. Describe the procedure in the optional
`metadata/methods.csv` registry. When the procedure varies by row, use a
categorical observation attribute bound with `sosa:usedProcedure`, and map its
codes to registered procedure IRIs.

Keep transformation workflow separate from observation method:

- A field or analytical procedure that produced an observation belongs in
  `methods.csv` and its measurement association.
- Code, notebooks, package environments, parameters, and run provenance that
  transformed source data into the SDP belong in `reproducibility/`.

Primary references:

- [I-ADOPT ontology 1.1](https://i-adopt.github.io/ontology/)
- [W3C/OGC SOSA/SSN](https://www.w3.org/TR/vocab-ssn/)
