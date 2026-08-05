# Salmon Data Package Template

This template is a draft authoring scaffold for Salmon Data Package metadata and data files.

Fill the CSVs under `metadata/` and place data CSV files under `data/`. The metadata CSV headers are generated from the authoritative Table Schemas and must stay exactly as provided, in order, with no extra columns. Optional, recommended, and conditional fields can be left blank when their rules allow.

Use `metadata/codes.csv` when any `metadata/column_dictionary.csv` row has `column_role` set to `categorical`. Published packages must include a generated `datapackage.json` and pass strict SDP validation; this blank template intentionally omits `datapackage.json`.

The template also includes optional `metadata/methods.csv` and paired files under
`metadata/structure/`. Delete `methods.csv` when no procedure registry is needed;
delete both structure files when no measure-specific bindings are needed. Use
the paired structure files when measures in a wide table have different logical
dimension sets. `methods.csv` describes SOSA procedures and does not add a
Method component to I-ADOPT.

An extended package may also add an optional top-level `reproducibility/`
directory with `reviewed_semantic_selections.csv`, `workflow/`, `provenance/`,
and `source/` sidecars. These document package creation and are not canonical
metadata resources.
