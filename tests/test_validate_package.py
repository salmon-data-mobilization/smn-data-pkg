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

from validate_package import Validator  # noqa: E402


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
