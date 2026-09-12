from __future__ import annotations

import csv
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from validate_package import (  # noqa: E402
    DESCRIPTOR_PROJECTED_COLUMNS,
    Validator,
    descriptor_annotation_keys,
    descriptor_field_from_column,
)

import generate_artifacts  # noqa: E402


# The seven keys both mirrors project into a descriptor field entry:
# metasalmon `.ms_descriptor_field_keys()` and metasalmonpy's descriptor
# projection (hub backlog #90, re-measured 2026-08-24). Pinned here so the
# schema-derived allowlist is shown to cover what the writers actually emit;
# this is the expectation, not the allowlist.
MIRROR_ANNOTATION_KEYS = (
    "unit_iri",
    "term_iri",
    "term_type",
    "property_iri",
    "entity_iri",
    "constraint_iri",
    "statistical_modifier_iri",
)

# A fixture placeholder in the namespace the minimal example already uses for
# its own placeholder terms (`https://w3id.org/example/salmon#...`). No shipped
# example carries a statistical_modifier_iri, so a fully annotated measurement
# column needs one that is not a term choice. Retire when an example carries
# a real smn:StatisticalModifierScheme concept and the test can copy it.
PLACEHOLDER_STATISTICAL_MODIFIER_IRI = (
    "https://w3id.org/example/salmon#TotalStatisticalModifierPlaceholder"
)


class StrictValidationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.package_path = Path(self.temp_dir.name) / "minimal-example"
        shutil.copytree(ROOT / "examples" / "minimal-example", self.package_path)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def errors(self) -> list[str]:
        return Validator(self.package_path).validate()

    def test_minimal_example_passes(self) -> None:
        self.assertEqual([], self.errors())

    def test_rejects_extra_metadata_header(self) -> None:
        path = self.package_path / "metadata" / "dataset.csv"
        rows = read_csv(path)
        rows[0]["extra_column"] = "not allowed"
        write_csv(path, rows, list(rows[0].keys()))

        self.assertHasError("header must exactly be")

    def test_rejects_partial_temporal_date(self) -> None:
        path = self.package_path / "metadata" / "dataset.csv"
        rows = read_csv(path)
        rows[0]["temporal_start"] = "1996-01"
        write_csv(path, rows, rows[0].keys())

        self.assertHasError("temporal_start must match pattern")

    def test_rejects_missing_categorical_code_coverage(self) -> None:
        path = self.package_path / "metadata" / "codes.csv"
        rows = [
            row
            for row in read_csv(path)
            if not (row["column_name"] == "FULL_CU_IN" and row["code_value"] == "CO-4")
        ]
        write_csv(path, rows, rows[0].keys())

        self.assertHasError("CO-4")

    def test_rejects_unsafe_table_path(self) -> None:
        path = self.package_path / "metadata" / "tables.csv"
        rows = read_csv(path)
        rows[0]["file_name"] = "../escape.csv"
        write_csv(path, rows, rows[0].keys())

        self.assertHasError("safe relative path")

    def test_rejects_descriptor_license_drift(self) -> None:
        path = self.package_path / "datapackage.json"
        descriptor = json.loads(path.read_text(encoding="utf-8"))
        descriptor["licenses"] = [{"name": "Open Government Licence - Canada"}]
        path.write_text(json.dumps(descriptor, indent=2) + "\n", encoding="utf-8")

        self.assertHasError("licenses must map")

    def test_descriptor_fields_may_carry_dictionary_annotation_keys(self) -> None:
        # Hub backlog #90, ruled 2026-08-24 (permit the keys): both mirrors
        # project the dictionary's term and I-ADOPT columns into the
        # descriptor field entry, and the whole-entry comparison rejected
        # every annotated package. A fully annotated measurement column, all
        # seven keys carried with the dictionary values, must pass.
        set_dictionary_cells(
            self.package_path,
            "NATURAL_SPAWNERS_TOTAL",
            {"statistical_modifier_iri": PLACEHOLDER_STATISTICAL_MODIFIER_IRI},
        )
        carried = carry_annotation_keys(
            self.package_path, "NATURAL_SPAWNERS_TOTAL", MIRROR_ANNOTATION_KEYS
        )
        self.assertEqual(set(MIRROR_ANNOTATION_KEYS), set(carried))

        self.assertEqual([], self.errors())

    def test_descriptor_field_rejects_key_that_is_not_a_dictionary_column(self) -> None:
        # Permitting the annotation keys must not open the entry to anything:
        # a key with no column_dictionary.csv column behind it stays invalid.
        edit_descriptor_field(
            self.package_path, "NATURAL_SPAWNERS_TOTAL", {"colour": "silver"}
        )

        self.assertHasError("'colour' is not a metadata/column_dictionary.csv column")

    def test_descriptor_annotation_key_must_agree_with_dictionary(self) -> None:
        # A carried key is a copy of the CSV cell; a copy that disagrees makes
        # the package invalid, exactly as a title or type drift does. The wrong
        # value is another IRI from the same row, not a new term.
        row = dictionary_row(self.package_path, "NATURAL_SPAWNERS_TOTAL")
        edit_descriptor_field(
            self.package_path, "NATURAL_SPAWNERS_TOTAL", {"unit_iri": row["term_iri"]}
        )

        self.assertHasError(
            "unit_iri must equal the metadata/column_dictionary.csv value"
        )

    def test_descriptor_annotation_value_is_compared_untrimmed(self) -> None:
        # B-90 review follow-up (P2): the spec says an annotation is carried
        # with the dictionary value unchanged, but the comparison stripped
        # the carried string first, so a padded IRI passed although it is
        # not the CSV cell and not an absolute IRI. A non-blank carried
        # value is compared exactly; the error names the entry and the key.
        row = dictionary_row(self.package_path, "NATURAL_SPAWNERS_TOTAL")
        padded = f" {row['unit_iri']} "
        edit_descriptor_field(
            self.package_path, "NATURAL_SPAWNERS_TOTAL", {"unit_iri": padded}
        )

        self.assertHasError(
            "schema.fields entry NATURAL_SPAWNERS_TOTAL: unit_iri must equal the "
            f"metadata/column_dictionary.csv value {row['unit_iri']!r}; found {padded!r}"
        )

    def test_descriptor_annotation_exact_value_passes(self) -> None:
        # The control for the padded case: the same key carried exactly.
        carried = carry_annotation_keys(
            self.package_path, "NATURAL_SPAWNERS_TOTAL", ("unit_iri",)
        )
        self.assertEqual(["unit_iri"], list(carried))

        self.assertEqual([], self.errors())

    def test_descriptor_blank_annotation_may_be_carried_empty_or_null(self) -> None:
        # A blank dictionary cell may be carried as "" or null (the spec's
        # "carried blank"); whitespace-only is neither, it is a changed value.
        row = dictionary_row(self.package_path, "NATURAL_SPAWNERS_TOTAL")
        self.assertEqual("", row["statistical_modifier_iri"])

        for blank in ("", None):
            edit_descriptor_field(
                self.package_path,
                "NATURAL_SPAWNERS_TOTAL",
                {"statistical_modifier_iri": blank},
            )
            self.assertEqual([], self.errors(), f"carried as {blank!r}")

        edit_descriptor_field(
            self.package_path, "NATURAL_SPAWNERS_TOTAL", {"statistical_modifier_iri": " "}
        )
        self.assertHasError(
            "statistical_modifier_iri must equal the metadata/column_dictionary.csv "
            "value ''; found ' '"
        )

    def test_descriptor_core_keys_must_still_match(self) -> None:
        # The core projection keeps its exact comparison after the refactor.
        edit_descriptor_field(
            self.package_path, "NATURAL_SPAWNERS_TOTAL", {"title": "Renamed"}
        )

        self.assertHasError("title must be 'Total natural spawners'")

    def test_descriptor_field_order_must_still_follow_the_dictionary(self) -> None:
        path = self.package_path / "datapackage.json"
        descriptor = json.loads(path.read_text(encoding="utf-8"))
        fields = data_resource(descriptor)["schema"]["fields"]
        fields.append(fields.pop(0))
        path.write_text(json.dumps(descriptor, indent=2) + "\n", encoding="utf-8")

        self.assertHasError(
            "schema.fields must match metadata/column_dictionary.csv-derived fields"
        )

    def test_descriptor_constraints_null_is_not_absent(self) -> None:
        # B-90 review follow-up: the spec table says `constraints` is absent
        # for a non-required column, and Table Schema says a carried
        # `constraints` must be an object. Comparing the core keys through
        # .get() made `null` equal to absent, so an entry the whole-entry
        # comparison had rejected passed strict validation. Presence is
        # compared as well as value, and the error names the entry and key.
        edit_descriptor_field(self.package_path, "POPULATION", {"constraints": None})

        self.assertHasError(
            "schema.fields entry POPULATION: constraints must be absent; found None"
        )

    def test_descriptor_required_column_still_carries_constraints(self) -> None:
        # The presence check leaves the required side alone: POP_ID is
        # required in the dictionary, its entry carries {"required": true},
        # and the package passes.
        self.assertEqual("TRUE", dictionary_row(self.package_path, "POP_ID")["required"])
        self.assertEqual(
            {"required": True}, descriptor_field(self.package_path, "POP_ID")["constraints"]
        )

        self.assertEqual([], self.errors())

    def assertHasError(self, expected: str) -> None:
        errors = self.errors()
        if not any(expected in error for error in errors):
            self.fail(f"Expected error containing {expected!r}; found {errors!r}")


class ObservationStructureValidationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.package_path = Path(self.temp_dir.name) / "mixed-grain-example"
        shutil.copytree(ROOT / "examples" / "mixed-grain-example", self.package_path)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_mixed_grain_example_passes(self) -> None:
        self.assertEqual([], self.errors())

    def test_structure_files_must_be_present_as_a_pair(self) -> None:
        (
            self.package_path
            / "metadata"
            / "structure"
            / "observation_components.csv"
        ).unlink()

        self.assertHasError("must be present together")

    def test_structure_requires_exactly_one_measure_component(self) -> None:
        path = (
            self.package_path
            / "metadata"
            / "structure"
            / "observation_components.csv"
        )
        rows = read_csv(path)
        for row in rows:
            if row["observation_structure_id"] == "total_spawners_by_brood":
                if row["component_role"] == "measure":
                    row["component_role"] = "dimension"
        write_csv(path, rows, rows[0].keys())

        self.assertHasError("must have exactly one measure component")

    def test_structure_requires_at_least_one_dimension_component(self) -> None:
        path = (
            self.package_path
            / "metadata"
            / "structure"
            / "observation_components.csv"
        )
        rows = read_csv(path)
        for row in rows:
            if row["observation_structure_id"] == "total_spawners_by_brood":
                if row["component_role"] == "dimension":
                    row["component_role"] = "attribute"
        write_csv(path, rows, rows[0].keys())

        self.assertHasError("must have at least one dimension component")

    def test_present_structure_extension_must_cover_every_measurement(self) -> None:
        structures_path = (
            self.package_path
            / "metadata"
            / "structure"
            / "observation_structures.csv"
        )
        structures = [
            row
            for row in read_csv(structures_path)
            if row["observation_structure_id"] != "total_spawners_by_brood"
        ]
        write_csv(structures_path, structures, structures[0].keys())

        components_path = (
            self.package_path
            / "metadata"
            / "structure"
            / "observation_components.csv"
        )
        components = [
            row
            for row in read_csv(components_path)
            if row["observation_structure_id"] != "total_spawners_by_brood"
        ]
        write_csv(components_path, components, components[0].keys())

        self.assertHasError("every measurement column")

    def test_measure_component_must_bind_a_measurement_column(self) -> None:
        path = self.package_path / "metadata" / "column_dictionary.csv"
        rows = read_csv(path)
        for row in rows:
            if row["column_name"] == "recruits":
                row["column_role"] = "attribute"
        write_csv(path, rows, rows[0].keys())

        self.assertHasError("must bind a measurement column")

    def test_required_component_must_be_present_when_measure_is_observed(self) -> None:
        dictionary_path = self.package_path / "metadata" / "column_dictionary.csv"
        dictionary_rows = read_csv(dictionary_path)
        for row in dictionary_rows:
            if row["column_name"] == "estimate_method":
                row["required"] = "FALSE"
        write_csv(dictionary_path, dictionary_rows, dictionary_rows[0].keys())

        data_path = self.package_path / "data" / "stock_recruit.csv"
        data_rows = read_csv(data_path)
        data_rows[0]["estimate_method"] = ""
        write_csv(data_path, data_rows, data_rows[0].keys())

        self.assertHasError("required_when_observed")

    def test_repeated_measure_must_be_invariant_at_declared_grain(self) -> None:
        path = self.package_path / "data" / "stock_recruit.csv"
        rows = read_csv(path)
        rows[1]["total_spawners"] = "101"
        write_csv(path, rows, rows[0].keys())

        self.assertHasError("conflicting values at dimension tuple")

    def test_dynamic_procedure_codes_require_registered_method_iris(self) -> None:
        path = self.package_path / "metadata" / "codes.csv"
        rows = read_csv(path)
        for row in rows:
            if row["code_value"] == "expanded_count":
                row["term_iri"] = ""
        write_csv(path, rows, rows[0].keys())

        self.assertHasError("sosa:usedProcedure code")

    def test_every_enumerated_procedure_code_requires_an_absolute_method_iri(self) -> None:
        # sdp-0.3.0 removed the metadata/methods.csv registry: an enumerated
        # sosa:usedProcedure code is valid when its term_iri is an absolute
        # shared-vocabulary IRI. The declared code list is the complete allowed
        # procedure domain, so a code no data row uses is still validated.
        path = self.package_path / "metadata" / "codes.csv"
        rows = read_csv(path)
        extra = dict(rows[0])
        extra["code_value"] = "unused_relative_method"
        extra["code_label"] = "Unused method with a relative IRI"
        extra["term_iri"] = "methods/not-absolute"
        rows.append(extra)
        write_csv(path, rows, rows[0].keys())

        self.assertHasError(
            "must be an absolute IRI resolving to a shared-vocabulary sosa:Procedure"
        )

    def test_static_method_reference_must_be_an_absolute_iri(self) -> None:
        # sdp-0.3.0 moved the static method reference from the column
        # dictionary to tables.csv method_iri; there is no local registry to
        # resolve against, so the structural contract is IRI shape.
        path = self.package_path / "metadata" / "tables.csv"
        rows = read_csv(path)
        for row in rows:
            if row["table_id"] == "stock_recruit":
                row["method_iri"] = "methods/not-absolute"
        write_csv(path, rows, rows[0].keys())

        self.assertHasError("method_iri must be an absolute IRI")

    def test_column_dictionary_rejects_removed_method_iri_column(self) -> None:
        # sdp-0.3.0 deleted the column_dictionary method_iri slot. The strict
        # header contract is what keeps it deleted: a package that still
        # carries the pre-0.3.0 column must be rejected, not silently ignored.
        path = self.package_path / "metadata" / "column_dictionary.csv"
        rows = read_csv(path)
        for row in rows:
            row["method_iri"] = ""
        rows[0]["method_iri"] = "https://example.org/methods/mark-recapture"
        write_csv(path, rows, list(rows[0].keys()))

        self.assertHasError("column_dictionary.csv header must exactly be")

    def test_descriptor_must_list_present_extended_metadata(self) -> None:
        # The optional extended metadata in sdp-0.3.0 is the structure pair;
        # when the files are present on disk the descriptor must list them.
        path = self.package_path / "datapackage.json"
        descriptor = json.loads(path.read_text(encoding="utf-8"))
        descriptor["resources"] = [
            resource
            for resource in descriptor["resources"]
            if resource.get("path") != "metadata/structure/observation_structures.csv"
        ]
        path.write_text(json.dumps(descriptor, indent=2) + "\n", encoding="utf-8")

        self.assertHasError(
            "resources must include metadata/structure/observation_structures.csv"
        )

    def test_bound_attributes_are_invariant_at_declared_grain(self) -> None:
        path = self.package_path / "data" / "stock_recruit.csv"
        rows = read_csv(path)
        duplicate = dict(rows[0])
        duplicate["estimate_method"] = "expanded_count"
        rows.append(duplicate)
        write_csv(path, rows, rows[0].keys())

        self.assertHasError("conflicting values at dimension tuple")

    def test_descriptor_fields_carry_semicolon_constraint_iri_unchanged(self) -> None:
        # Both measurement columns carry two semicolon-separated constraint
        # IRIs; the descriptor carries the dictionary string as-is, not a
        # split list, and passes.
        for column_name in ("total_spawners", "recruits"):
            carried = carry_annotation_keys(
                self.package_path, column_name, MIRROR_ANNOTATION_KEYS
            )
            self.assertIn("constraint_iri", carried)
            self.assertIn(";", carried["constraint_iri"])

        self.assertEqual([], self.errors())

    def test_numeric_lexical_variants_are_equal_for_grain_invariance(self) -> None:
        dictionary_path = self.package_path / "metadata" / "column_dictionary.csv"
        dictionary = read_csv(dictionary_path)
        for row in dictionary:
            if row["column_name"] == "total_spawners":
                row["value_type"] = "number"
        write_csv(dictionary_path, dictionary, dictionary[0].keys())

        descriptor_path = self.package_path / "datapackage.json"
        descriptor = json.loads(descriptor_path.read_text(encoding="utf-8"))
        for resource in descriptor["resources"]:
            if resource.get("path") != "data/stock_recruit.csv":
                continue
            for field in resource["schema"]["fields"]:
                if field.get("name") == "total_spawners":
                    field["type"] = "number"
        descriptor_path.write_text(
            json.dumps(descriptor, indent=2) + "\n",
            encoding="utf-8",
        )

        data_path = self.package_path / "data" / "stock_recruit.csv"
        rows = read_csv(data_path)
        rows[1]["total_spawners"] = "100.0"
        write_csv(data_path, rows, rows[0].keys())

        self.assertEqual([], self.errors())

    def errors(self) -> list[str]:
        return Validator(self.package_path).validate()

    def assertHasError(self, expected: str) -> None:
        errors = self.errors()
        if not any(expected in error for error in errors):
            self.fail(f"Expected error containing {expected!r}; found {errors!r}")


class DescriptorAllowlistTests(unittest.TestCase):
    """The permitted descriptor keys come from the schema, not a hand list."""

    def setUp(self) -> None:
        self.schema = generate_artifacts.load_schema_bundle()["metadata_schemas"][
            "column_dictionary"
        ]

    def test_allowlist_is_every_dictionary_column_the_projection_does_not_express(
        self,
    ) -> None:
        expected = [
            field["name"]
            for field in self.schema["fields"]
            if field["name"] not in DESCRIPTOR_PROJECTED_COLUMNS
        ]
        self.assertEqual(expected, descriptor_annotation_keys(self.schema))
        self.assertTrue(
            set(MIRROR_ANNOTATION_KEYS).issubset(descriptor_annotation_keys(self.schema))
        )

    def test_allowlist_follows_a_column_added_to_the_schema(self) -> None:
        # The reason the list is derived: statistical_modifier_iri arrived in
        # sdp-0.3.0 and a hand-written list in the script would have missed
        # it. A column that does not exist yet is permitted the moment the
        # schema carries it.
        schema = json.loads(json.dumps(self.schema))
        schema["fields"].append(
            {"name": "future_component_iri", "type": "string", "description": "x"}
        )
        self.assertIn("future_component_iri", descriptor_annotation_keys(schema))
        self.assertNotIn("future_component_iri", descriptor_annotation_keys(self.schema))

    def test_projected_columns_are_all_schema_columns(self) -> None:
        names = {field["name"] for field in self.schema["fields"]}
        self.assertTrue(set(DESCRIPTOR_PROJECTED_COLUMNS).issubset(names))

    def test_expected_field_carries_non_blank_annotations_only(self) -> None:
        column = {
            "dataset_id": "d",
            "table_id": "t",
            "column_name": "x",
            "column_label": "X",
            "column_description": "An x",
            "column_role": "measurement",
            "value_type": "number",
            "required": "TRUE",
            "unit_iri": "https://qudt.org/vocab/unit/INDIV",
            "statistical_modifier_iri": "",
        }
        field = descriptor_field_from_column(column, self.schema)
        self.assertEqual(
            {
                "name": "x",
                "title": "X",
                "description": "An x",
                "type": "number",
                "constraints": {"required": True},
                "column_role": "measurement",
                "unit_iri": "https://qudt.org/vocab/unit/INDIV",
            },
            field,
        )


class ProfileTests(unittest.TestCase):
    def test_generated_profile_has_no_tabular_data_package_ref(self) -> None:
        profile_text = (
            ROOT / "profiles" / "salmon-data-package" / "v0.2" / "profile.json"
        ).read_text(encoding="utf-8")
        self.assertNotIn("tabular-data-package", profile_text)

    def test_extended_metadata_resources_are_optional(self) -> None:
        profile = json.loads(
            (
                ROOT
                / "profiles"
                / "salmon-data-package"
                / "v0.2"
                / "profile.json"
            ).read_text(encoding="utf-8")
        )
        resources = {
            resource["path"]: resource
            for resource in profile["sdp:metadataResources"]
        }
        extended_paths = {
            "metadata/methods.csv",
            "metadata/structure/observation_structures.csv",
            "metadata/structure/observation_components.csv",
        }
        self.assertEqual(
            {path: "optional" for path in extended_paths},
            {path: resources[path]["sdp:requirement"] for path in extended_paths},
        )

        required_paths = {
            clause["properties"]["resources"]["contains"]["properties"]["path"]["const"]
            for clause in profile["allOf"]
        }
        self.assertTrue(extended_paths.isdisjoint(required_paths))


def data_resource(descriptor: dict) -> dict:
    for resource in descriptor["resources"]:
        if resource.get("path", "").startswith("data/"):
            return resource
    raise AssertionError("descriptor has no data resource")


def dictionary_row(package_path: Path, column_name: str) -> dict[str, str]:
    for row in read_csv(package_path / "metadata" / "column_dictionary.csv"):
        if row["column_name"] == column_name:
            return row
    raise AssertionError(f"no column_dictionary.csv row for {column_name}")


def set_dictionary_cells(package_path: Path, column_name: str, cells: dict[str, str]) -> None:
    path = package_path / "metadata" / "column_dictionary.csv"
    rows = read_csv(path)
    for row in rows:
        if row["column_name"] == column_name:
            row.update(cells)
    write_csv(path, rows, rows[0].keys())


def descriptor_field(package_path: Path, column_name: str) -> dict:
    descriptor = json.loads((package_path / "datapackage.json").read_text(encoding="utf-8"))
    for field in data_resource(descriptor)["schema"]["fields"]:
        if field.get("name") == column_name:
            return field
    raise AssertionError(f"no datapackage.json field entry for {column_name}")


def edit_descriptor_field(package_path: Path, column_name: str, keys: dict) -> None:
    path = package_path / "datapackage.json"
    descriptor = json.loads(path.read_text(encoding="utf-8"))
    for field in data_resource(descriptor)["schema"]["fields"]:
        if field.get("name") == column_name:
            field.update(keys)
    path.write_text(json.dumps(descriptor, indent=2) + "\n", encoding="utf-8")


def carry_annotation_keys(package_path: Path, column_name: str, keys) -> dict[str, str]:
    """Copy the non-blank dictionary cells named by keys onto the descriptor field."""
    row = dictionary_row(package_path, column_name)
    carried = {key: row[key] for key in keys if row.get(key, "") != ""}
    edit_descriptor_field(package_path, column_name, carried)
    return carried


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows, fieldnames) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(fieldnames), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


if __name__ == "__main__":
    unittest.main()
