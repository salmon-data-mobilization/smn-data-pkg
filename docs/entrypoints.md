# Entrypoints (What Is Actually Used?)

Purpose: keep one short, reliable map of what starts the system, what is wired in, and where to edit things.

## Build

- Build command(s): `python3 scripts/generate_artifacts.py --write`

## Test

- Test command(s): `python3 -m unittest discover -s tests -v` and `python3 scripts/generate_artifacts.py --check`
- Fastest smoke test: `python3 scripts/validate_package.py examples/minimal-example`

## Canonical Implementations (Per Feature)

- SDP validity rules (normative, meaning rules that define validity) → `SPECIFICATION.md`
- Authoritative metadata schemas → `schema/frictionless/metadata/*.schema.json`
- SDP Frictionless profile → `profiles/salmon-data-package/v0.3/profile.json` (prior version directories such as `v0.2/` are frozen published contracts, never edited)
- Custom cross-table/domain rules → `schema/sdp.rules.yaml`
- Generated blank template → `templates/salmon-data-package-template/` + `templates/salmon-data-package-template.zip`
- Generated field reference → `docs/field-reference.md`
- Column metadata schema + measurement requirements → `SPECIFICATION.md` + `schema/frictionless/metadata/column_dictionary.schema.json` + `schema/sdp.rules.yaml`
- Categorical codes meaning (canonical labels/IRIs live in codes.csv) → `SPECIFICATION.md` + `schema/frictionless/metadata/codes.schema.json` + `schema/sdp.rules.yaml`
- SOSA procedure references (sdp-0.3.0 removed the `metadata/methods.csv` registry) → `SPECIFICATION.md` + `schema/frictionless/metadata/tables.schema.json` (`method_iri`) + `schema/frictionless/metadata/codes.schema.json` (`term_iri` for row-varying procedures) + `docs/i-adopt-integration-guide.md`
- Mixed-grain measure/dimension bindings → `schema/frictionless/metadata/observation_*.schema.json` + `schema/sdp.rules.yaml` + `docs/observation-structure-guide.md`
- Reproducibility sidecar layout → `SPECIFICATION.md` + `examples/mixed-grain-example/reproducibility/`
- Human quickstart guide → `README.md` ("Quick Start" section; no separate quickstart document exists under docs/)
- Tooling and LLM (text-generating AI system) guidance → `AGENTS.md`
- Worked core example package → `examples/minimal-example/`
- Worked extended example package → `examples/mixed-grain-example/`
