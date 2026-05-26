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


class ProfileTests(unittest.TestCase):
    def test_generated_profile_has_no_tabular_data_package_ref(self) -> None:
        profile_text = (
            ROOT / "profiles" / "salmon-data-package" / "v0.2" / "profile.json"
        ).read_text(encoding="utf-8")
        self.assertNotIn("tabular-data-package", profile_text)


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
