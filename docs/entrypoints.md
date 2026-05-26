# Entrypoints (What Is Actually Used?)

Purpose: keep one short, reliable map of what starts the system, what is wired in, and where to edit things.

## Build

- Build command(s): `python3 scripts/generate_artifacts.py --write`

## Test

- Test command(s): `python3 scripts/generate_artifacts.py --check`
- Fastest smoke test: `python3 scripts/generate_artifacts.py --check`

## Canonical Implementations (Per Feature)

- SDP validity rules (normative, meaning rules that define validity) → `SPECIFICATION.md`
- Authoritative metadata schemas → `schema/frictionless/metadata/*.schema.json`
- SDP Frictionless profile → `profiles/salmon-data-package/v0.2/profile.json`
- Custom cross-table/domain rules → `schema/sdp.rules.yaml`
- Generated blank template → `templates/salmon-data-package-template/` + `templates/salmon-data-package-template.zip`
- Generated field reference → `docs/field-reference.md`
- Column metadata schema + measurement requirements → `SPECIFICATION.md` + `schema/frictionless/metadata/column_dictionary.schema.json` + `schema/sdp.rules.yaml`
- Categorical codes meaning (canonical labels/IRIs live in codes.csv) → `SPECIFICATION.md` + `schema/frictionless/metadata/codes.schema.json` + `schema/sdp.rules.yaml`
- Human quickstart guide → `docs/quickstart.md`
- Tooling and LLM (text-generating AI system) guidance → `docs/implementation-guide.md`
- Worked example package → `examples/minimal-example/metadata/column_dictionary.csv`
