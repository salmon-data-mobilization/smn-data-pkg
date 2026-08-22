# Salmon Data Package Template

This template is a draft authoring scaffold for Salmon Data Package metadata and data files.

Fill the CSVs under `metadata/` and place data CSV files under `data/`. The metadata CSV headers are generated from the authoritative Table Schemas and must stay exactly as provided, in order, with no extra columns. Optional, recommended, and conditional fields can be left blank when their rules allow.

Use `metadata/codes.csv` when any `metadata/column_dictionary.csv` row has `column_role` set to `categorical`. Published packages must include a generated `datapackage.json` and pass strict SDP validation; this blank template intentionally omits `datapackage.json`.

The template also includes optional paired files under `metadata/structure/`
(`metadata/structure/observation_structures.csv` and
`metadata/structure/observation_components.csv`). Delete both structure files
when no measure-specific bindings are needed; use them when measures in a wide
table have different logical dimension sets. Method references have no
registry file: a table-level method lives in `metadata/tables.csv`
(`method_iri`), and a row-varying procedure column binds `sosa:usedProcedure`
with its enumerated `metadata/codes.csv` term IRIs resolving to
shared-vocabulary SOSA Procedure concepts.

An extended package may also add an optional top-level `reproducibility/`
directory with `reviewed_semantic_selections.csv`, `workflow/`, `provenance/`,
and `source/` sidecars. These document package creation and are not canonical
metadata resources.
