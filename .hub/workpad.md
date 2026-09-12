# Workpad: B-90

## Queue item

**B-90** — Permit the I-ADOPT descriptor keys in smn-data-pkg's publication
validator. Repo `smn-data-pkg`, severity P2, legacy `#90`. Evidence:
metasalmon `knowledge/backlog.md`, entry `#90`, including the 2026-08-24
ruling (Brett, hub Q3: permit the keys, derive the allowlist from
`column_dictionary.schema.json`) and the 2026-08-21/2026-08-24 "identical
keys" corrections. Retires when an SDP with a fully annotated measurement
column passes `scripts/validate_package.py`, `SPECIFICATION.md` says
descriptor `schema.fields` entries may carry the I-ADOPT keys, and
`descriptor_field_from_column()` derives the allowlist from the schema.

## What changed and where

- `scripts/validate_package.py`
  - New `DESCRIPTOR_PROJECTED_COLUMNS`: the dictionary columns the core
    projection consumes (`dataset_id`/`table_id` as resource identity;
    `column_name→name`, `column_label→title`, `column_description→description`,
    `value_type→type`, `required→constraints`). This is the projection
    contract the script must own, not a copy of the dictionary contract.
  - New `descriptor_annotation_keys(schema)`: the permitted extra keys,
    derived at run time as every field of `column_dictionary.schema.json`
    not in the projected set. No hand-written list. Today that yields
    `column_role, unit_label, unit_iri, term_iri, term_type, property_iri,
    entity_iri, constraint_iri, statistical_modifier_iri`, which covers the
    seven keys both mirrors emit (metasalmon `.ms_descriptor_field_keys()`,
    `R/metadata-write.R:43-53`) plus `column_role` and `unit_label`. I did
    not carve those two out: any rule excluding them while keeping
    `term_type` (not an `_iri`) would be a second hand-written list, which
    is the thing the ruling said not to build. If Brett wants the allowlist
    narrower, the cut is one entry in `DESCRIPTOR_PROJECTED_COLUMNS`-style
    exclusion and a spec sentence; flagged in the PR.
  - `descriptor_field_from_column(column, schema)` now takes the schema and
    adds each permitted annotation key whose dictionary cell is non-blank.
  - New `descriptor_field_issues(field, expected, annotation_keys)`
    replaces the whole-list `!=`: core keys must match exactly (as before);
    an extra key must be a permitted annotation key (the descriptor MAY carry
    it) and, when carried, must equal the dictionary cell (blank cell may be
    carried as `""` or `null`); a key with no dictionary column behind it is
    an error. Field order and count are still checked first, with the
    original "schema.fields must match metadata/column_dictionary.csv-derived
    fields" message; per-entry errors now name the entry and the key.
- `SPECIFICATION.md`: new subsection "Data resource field entries" under
  the `datapackage.json` guidance stating the core projection table, that a
  field entry **may** carry the term and I-ADOPT keys, that the governing
  rule is "every dictionary column the core projection does not express, read
  from the schema", that a blank cell is omitted or carried blank, and that an
  unknown key or a disagreeing value is invalid. The "Versioning and
  extensions" bullet now also says unknown field-entry keys are rejected.
- `CHANGELOG.md`: `[Unreleased]` → `### Changed` entry in the existing style.
- `tests/test_validate_package.py`: ten new tests (23 → 33).
  - `StrictValidationTests` (minimal example): fully annotated measurement
    column with all seven keys passes; unknown key rejected; carried value
    that disagrees with the CSV rejected; core key drift still rejected;
    field order drift still rejected.
  - `ObservationStructureValidationTests` (mixed-grain example): both
    measurement columns carry their semicolon-separated `constraint_iri`
    unchanged and pass.
  - New `DescriptorAllowlistTests`: allowlist equals schema fields minus the
    projected set and covers the mirrors' seven keys; a column added to a
    (copied) schema is permitted without a script change; the projected
    columns all exist in the schema; the expected entry carries only
    non-blank annotations.
  - Helpers `data_resource`, `dictionary_row`, `set_dictionary_cells`,
    `edit_descriptor_field`, `carry_annotation_keys`.

**IRIs used in fixtures, and where they come from.** Every IRI the tests
carry is copied from the row it annotates in the shipped examples
(`examples/minimal-example/metadata/column_dictionary.csv` row
`NATURAL_SPAWNERS_TOTAL`; `examples/mixed-grain-example` rows
`total_spawners` and `recruits`). The one exception is
`statistical_modifier_iri`: no shipped example carries one, so the
"fully annotated" test sets a **placeholder** in the namespace the minimal
example already uses for its own placeholders
(`https://w3id.org/example/salmon#TotalStatisticalModifierPlaceholder`).
It exists only inside the test, is not written to any example or template,
and is not an ontology term choice. The "disagreeing value" test uses the
same row's `term_iri` as the wrong `unit_iri` rather than inventing one.
No ontology term IRI was chosen, changed, or removed by this change.

metasalmon's copy of the schema
(`inst/extdata/schema/frictionless/metadata/column_dictionary.schema.json`)
was diffed against `schema/frictionless/metadata/column_dictionary.schema.json`
and is byte-identical; nothing to report there.

## Commands run and results

All inside the worktree, Python 3.11.15, jsonschema 4.26.0, pytest 9.1.1.

Baseline on `origin/main` (47f0e81) before any edit:

    python3 -m pytest tests -q                       → 23 passed
    python3 scripts/validate_package.py examples/minimal-example      → passed
    python3 scripts/validate_package.py examples/mixed-grain-example  → passed
    python3 scripts/generate_artifacts.py --check    → in sync

**Failing before** (tests written, validator untouched):

    python3 -m pytest tests -q
        from validate_package import (  # noqa: E402
    E   ImportError: cannot import name 'DESCRIPTOR_PROJECTED_COLUMNS' from 'validate_package' (/home/user/hub-worktrees/salmon-data-mobilization-smn-data-pkg-B-90/scripts/validate_package.py)
    =========================== short test summary info ============================
    ERROR tests/test_validate_package.py
    !!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
    1 error in 0.27s

The import error is the new API not existing yet; the behavioural
reproduction is the minimal example copied to a scratch directory, its
`NATURAL_SPAWNERS_TOTAL` dictionary row given the placeholder
`statistical_modifier_iri`, and the matching descriptor field given all
seven keys with the dictionary values, then the **unmodified** validator:

    python3 scripts/validate_package.py <scratch>/b90-annotated-pkg
    Strict SDP validation failed for /tmp/claude-0/-home-user-metasalmon/c65e9c22-7ec7-5a53-8177-deda0f189418/scratchpad/b90-annotated-pkg:
    - datapackage.json resource data/nuseds-fraser-coho-sample.csv schema.fields must match metadata/column_dictionary.csv-derived fields.
    exit 1

That is the error the backlog entry reproduced end to end on 2026-08-21.

**Passing after** (validator, spec, changelog changed):

    python3 -m pytest tests -q                       → 33 passed
    python3 -m unittest discover -s tests            → Ran 33 tests, OK
    python3 scripts/validate_package.py <scratch>/b90-annotated-pkg
    Strict SDP validation passed: /tmp/claude-0/-home-user-metasalmon/c65e9c22-7ec7-5a53-8177-deda0f189418/scratchpad/b90-annotated-pkg
    exit 0
    python3 scripts/validate_package.py examples/minimal-example      → passed
    python3 scripts/validate_package.py examples/mixed-grain-example  → passed
    python3 scripts/generate_artifacts.py --check    → in sync
    git diff --check                                 → clean

CI (`.github/workflows/ci.yml`) runs exactly `python -m pytest tests/` and
`python scripts/generate_artifacts.py --check`; both were run here. The
`.pre-commit-config.yaml` hook is the same artifact check.

Edge cases exercised directly against `descriptor_field_issues()` (not
committed as tests, recorded here): a blank dictionary cell carried as
`null` or `""` → no issue; `constraint_iri` carried as a JSON list → value
mismatch (the spec says the string stays one string); a spurious
`constraints: {required: false}` → core mismatch, as before; a non-object
entry → "must be an object"; an unknown key → named, with the permitted list.

## What I did not do, and why

- Did not add the annotation keys to the shipped examples' `datapackage.json`
  or to the template. The keys are "may", the examples are valid without
  them, and the item's retirement condition is satisfied by the validator,
  the spec, and a test fixture. Changing example descriptors is a visible
  artifact change worth its own review (see candidates).
- Did not narrow the allowlist to exactly the seven mirror keys (see above).
- Did not touch `docs/i-adopt-integration-guide.md` or `docs/field-reference.md`
  (generated; unchanged because the schema is unchanged).
- Did not change the schema file. A schema-side marker (e.g. an `sdp:`
  annotation naming descriptor keys) would have been another way to derive
  the list, but it would change a file metasalmon vendors byte-identically
  and would need a re-vendor there.
- Did not edit anything in metasalmon, metasalmonpy, or `queue/`.

## Belongs to another item, or a candidate new item

- **Candidate (smn-data-pkg):** neither shipped example carries a
  `statistical_modifier_iri`, so no example demonstrates the fifth I-ADOPT
  component or a descriptor carrying the annotation keys. Adding one means
  choosing a real `smn:StatisticalModifierScheme` concept for
  `NATURAL_SPAWNERS_TOTAL` or `total_spawners`, which is a term selection
  needing appraisal rather than a by-product of this change.
- **Candidate (smn-data-pkg, question for Brett):** whether `column_role`
  and `unit_label` should be permitted descriptor keys. Under the
  schema-derived rule they are; the mirrors do not emit them; nothing is
  harmed either way.
- **metasalmon / metasalmonpy:** no port is owed. Neither vendors
  `validate_package.py`; metasalmon's schema copy is identical. The backlog
  `#90` entry's second retirement clause (metasalmonpy's seventh key matching
  R's) was already recorded closed on 2026-08-24. The queue item's state
  change and the backlog entry's retirement note are the hub's to make, not
  this branch's.

## Retirement conditions of anything added that silences or routes around a signal

- `PLACEHOLDER_STATISTICAL_MODIFIER_IRI` (test fixture): retires when a
  shipped example carries a real statistical-modifier concept and the test
  copies it from the example row like every other IRI it uses.
- `MIRROR_ANNOTATION_KEYS` (test pin of the seven keys the mirrors emit):
  retires when the mirrors' projections are themselves derived from the
  schema and a cross-repo check replaces the pin; until then it is the
  evidence that the derived allowlist covers what the writers actually emit.
- Blank cell carried as `null`/`""` accepted as agreeing with the CSV: a
  rule, not a guard, but stated so it can be tightened. Retires (tightens to
  "omit") if the spec later says blank keys must be omitted, or if a writer
  is found emitting blanks in some other shape that this leniency hides.
- The original "schema.fields must match ...-derived fields" message is kept
  for order/count mismatch so existing readers of the validator output (the
  backlog entry quotes it) still find it. Retires when nothing cites it.

## Follow-up: review finding (P3), `"constraints": null` read as absent

**Finding** (independent review of PR #7, reproduced here). `descriptor_field_issues()`
compared each core key with `field.get(key) != expected.get(key)`, so an
entry carrying `"constraints": null` for a **non-required** column compared
equal to an expected entry with no `constraints` key. The whole-entry `!=`
it replaced rejected that entry, the spec table this PR adds says "otherwise
the key is absent", and Table Schema requires `constraints` to be an object
— so the branch enforced less than the spec it introduced, and a
Frictionless-invalid entry passed strict publication validation.

Reproduction: minimal example copied to scratch, `"constraints": null` set
on the `POPULATION` entry (`required = FALSE`).

    origin/main (47f0e81) validator:
      - datapackage.json resource data/nuseds-fraser-coho-sample.csv schema.fields must match metadata/column_dictionary.csv-derived fields.   exit 1
    branch before the fix:
      Strict SDP validation passed: .../constraints-null-pkg                exit 0

**Fix.** `descriptor_field_issues()` compares presence as well as value for
each core key — `(key in field) != (key in expected) or field.get(key) !=
expected.get(key)` — and reuses the existing "must be absent; found ..."
message; the docstring says why. The annotation-key branch (a blank cell
carried as `""` or `null`) is untouched and keeps its retirement note above.
`SPECIFICATION.md` is unchanged: it already states the rule the fix now
enforces. `CHANGELOG.md`: one sentence added to the existing `[Unreleased]`
bullet.

**Tests** (`tests/test_validate_package.py`, 33 → 35, plus a `descriptor_field()`
reader helper): `test_descriptor_constraints_null_is_not_absent` (null on
`POPULATION` is rejected with a message naming the entry and the key) and
`test_descriptor_required_column_still_carries_constraints` (`POP_ID` is
required, its entry carries `{"required": true}`, the package passes).

    RED (tests written, validator unfixed):
      FAILED tests/test_validate_package.py::StrictValidationTests::test_descriptor_constraints_null_is_not_absent
      AssertionError: Expected error containing 'schema.fields entry POPULATION: constraints must be absent; found None'; found []
      1 failed, 34 passed
    GREEN (validator fixed):
      python3 -m pytest tests -q                       → 35 passed
      reproduction package:
      - datapackage.json resource data/nuseds-fraser-coho-sample.csv schema.fields entry POPULATION: constraints must be absent; found None.   exit 1
      python3 scripts/validate_package.py examples/minimal-example      → passed
      python3 scripts/validate_package.py examples/mixed-grain-example  → passed
      python3 scripts/generate_artifacts.py --check    → in sync
      git diff --check                                 → clean

**Second finding (Codex, P2), carried annotation values compared after
trimming.** `descriptor_field_issues()` compared `normalize_cell(carried)`
to the CSV value, so `" https://qudt.org/vocab/unit/INDIV "` passed although
it differs from the cell and is not an absolute IRI, while the spec text
this PR adds says the value is carried unchanged. Fix: a non-blank carried
string is compared exactly, untrimmed. Baseline decided and stated in the
code comment: the expected side is the CSV cell as `read_metadata_csv()`
loads it — `normalize_cell()` strips every metadata cell on read, and
`descriptor_field_from_column()` strips again — so the stripped cell is
the only rendering of the CSV value the validator holds and is the right
baseline. Blank/null handling kept exactly: a blank cell may be carried as
`""` or `null`; whitespace-only is neither and is now rejected as a changed
value. Tests (35 → 38): `test_descriptor_annotation_value_is_compared_untrimmed`
(padded `unit_iri` on `NATURAL_SPAWNERS_TOTAL` rejected, message names the
entry and key), `test_descriptor_annotation_exact_value_passes`, and
`test_descriptor_blank_annotation_may_be_carried_empty_or_null` — the
blank/null cases the first pass only exercised by hand (recorded above) are
now committed. `CHANGELOG.md` unchanged: the existing bullet's "a carried
value must equal the CSV cell" is now literally what the code does.

    RED (tests written, comparison unfixed):
      FAILED ...::test_descriptor_annotation_value_is_compared_untrimmed
        Expected error containing "schema.fields entry NATURAL_SPAWNERS_TOTAL: unit_iri must equal the metadata/column_dictionary.csv value 'https://qudt.org/vocab/unit/INDIV'; found ' https://qudt.org/vocab/unit/INDIV '"; found []
      FAILED ...::test_descriptor_blank_annotation_may_be_carried_empty_or_null
        Expected error containing "statistical_modifier_iri must equal the metadata/column_dictionary.csv value ''; found ' '"; found []
      2 failed, 36 passed
    GREEN (comparison fixed):
      python3 -m pytest tests -q                       → 38 passed
      python3 -m unittest discover -s tests            → Ran 38 tests, OK
      python3 scripts/validate_package.py examples/minimal-example      → passed
      python3 scripts/validate_package.py examples/mixed-grain-example  → passed
      python3 scripts/generate_artifacts.py --check    → in sync
      git diff --check                                 → clean
