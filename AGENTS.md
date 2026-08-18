## Project Notes (user-maintained)

**This file is git-tracked on purpose — do not add it to `.gitignore`.** It was
ignored from the initial commit until 2026-08-17, with no recorded rationale and
sitting in a block of editor and scratch-note patterns, so the effect was that
guidance binding contributors could not be read by them, reviewed in a PR, or
seen by anyone cloning the repo. The sibling repos state the same rule
(`metasalmon`, `metasalmonpy`).


### Project Overview

**Planning docs:** Ignore files in `docs/plans/` unless you are actively working from or on a specific ExecPlan; they are otherwise non-canonical.

**Salmon Data Package (SDP) Specification** - A lightweight, frictionless-style specification for exchanging salmon datasets between scientists, assessment biologists, and data stewards. The project's main goals are:

1. **Machine-aided data integration**: Enable automated validation, linking, and integration of salmon datasets through semantic metadata
2. **Semantic clarity for humans and machines**: Use ontology-linked IRIs (Internationalized Resource Identifiers) to provide both human-readable and machine-readable definitions
3. **Standard formats for automation and data sharing**: Provide a consistent, tool-friendly format that works with Excel/CSV while enabling programmatic access

**Core Architecture**:

- CSV metadata files: `dataset.csv`, `tables.csv`, `column_dictionary.csv`, `codes.csv` (required only when categorical columns exist)
- Links to DFO Salmon Ontology, Salmon Domain Ontology, or other controlled vocabularies or ontologies via IRIs for semantic interoperability
- Compatible with Frictionless Data Package specification
- Supports controlled vocabularies (SKOS, NCBI taxonomy, Darwin Core, etc.)
- Designed for incremental adoption - existing tables can be wrapped with minimal changes

**Related Projects**:

- `metasmn` R package for reading, validating, and working with SDP packages
- `dfo-salmon-ontology` providing semantic definitions
- `salmon-knowledge-commons` holding source-backed knowledge about salmon itself, and the register of ontology gaps

### Recording durable salmon knowledge

When work on this spec establishes something durable about **salmon** — what a
term actually means, why a field is modelled the way it is, how two vocabularies
relate — write it to `salmon-knowledge-commons`, not to a PR description, a
commit message, or a chat transcript. Those evaporate, and the next person
re-derives it.

This spec is where the ambiguity surfaces first: a column definition is often the
moment someone discovers that a label means two different things in two agencies.
That discovery is the durable part, and it is worth more than the column.

- **If you can push there, open a PR.** If you cannot, put the finding in your
  report **with its sources** so a maintainer can.
- **Source-backed claims only.** The commons rejects a claim with no citation.
- **Never assert your own verification.** `generated` says who wrote a card;
  `verified` says who independently checked it. They are different actors.
- **Ontology gaps go there too** — a concept with no term in `smn`,
  `gcdfo` or the PSC CV, with a note saying what a term would have to say and
  where it should be minted. That register feeds the term-request pipeline.

### Build and Test Commands

### Code Style Commands

### Testing Instructions

### Security Instructions
