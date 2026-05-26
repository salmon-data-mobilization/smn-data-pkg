# Salmon Data Package Template

This template is a draft authoring scaffold for Salmon Data Package metadata and data files.

Fill the CSVs under `metadata/` and place data CSV files under `data/`. The metadata CSV headers are generated from the authoritative Table Schemas and must stay exactly as provided, in order, with no extra columns. Optional, recommended, and conditional fields can be left blank when their rules allow.

Use `metadata/codes.csv` when any `metadata/column_dictionary.csv` row has `column_role` set to `categorical`. Published packages must include a generated `datapackage.json` and pass strict SDP validation; this blank template intentionally omits `datapackage.json`.
