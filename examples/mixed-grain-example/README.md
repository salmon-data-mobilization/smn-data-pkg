# Mixed-grain observation structure example

This SDP demonstrates two measures stored in one wide table at different logical
grains. `total_spawners` is identified by stock and brood year, while `recruits`
is identified by stock, brood year, return year, and age. The repeated
`total_spawners` value must therefore be invariant within its declared dimension
tuple.

The example also shows both procedure patterns:

- `column_dictionary.method_iri` associates one fixed SOSA Procedure with every
  non-empty value of `total_spawners`.
- `estimate_method` is a row-varying attribute bound with
  `sosa:usedProcedure`; its code IRIs resolve to rows in `metadata/methods.csv`.

The files under `reproducibility/` are optional sidecars. They preserve review
and workflow context but do not alter SDP observation semantics.
