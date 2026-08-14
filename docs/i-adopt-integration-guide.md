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

SDP records methods outside the column dictionary entirely (sdp-0.3.0): a
method describes how an observation was made, not what was observed, which is
also why I-ADOPT defines no Method component. Record the protocol or method at
the table level (`tables.csv` `protocol_iri`/`protocol_citation`/`method_iri`),
or — when the procedure varies by row — as a coded data column bound with
`sosa:usedProcedure`. The column dictionary's fifth I-ADOPT component column is
`statistical_modifier_iri` (`iop:StatisticalModifier`).

Keep transformation workflow separate from observation method:

- A field or analytical procedure that produced an observation belongs in
  the table-level protocol/method fields or the row-varying
  `sosa:usedProcedure` pattern.
- Code, notebooks, package environments, parameters, and run provenance that
  transformed source data into the SDP belong in `reproducibility/`.

Primary references:

- [I-ADOPT ontology 1.1](https://i-adopt.github.io/ontology/)
- [W3C/OGC SOSA/SSN](https://www.w3.org/TR/vocab-ssn/)
