#!/usr/bin/env python3
"""Strict publication validator for Salmon Data Package directories."""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from collections import defaultdict
from dataclasses import dataclass
from datetime import date, datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path, PurePosixPath
from typing import Iterable
from urllib.parse import urlparse

import jsonschema

import generate_artifacts


TABLE_ORDER = generate_artifacts.TABLE_ORDER
PROFILE_URL = generate_artifacts.PROFILE_URL
SOSA_USED_PROCEDURE = "http://www.w3.org/ns/sosa/usedProcedure"

KNOWN_LICENSES = {
    "Open Government Licence - Canada": {
        "name": "OGL-Canada-2.0",
        "title": "Open Government Licence - Canada",
        "path": "https://open.canada.ca/en/open-government-licence-canada",
    },
    "CC-BY-4.0": {
        "name": "CC-BY-4.0",
        "title": "Creative Commons Attribution 4.0 International",
        "path": "https://creativecommons.org/licenses/by/4.0/",
    },
}

IRI_FIELDS = {
    "tables": ("observation_unit_iri",),
    "column_dictionary": (
        "unit_iri",
        "term_iri",
        "property_iri",
        "entity_iri",
        "constraint_iri",
        "method_iri",
    ),
    "codes": ("vocabulary_iri", "term_iri"),
    "methods": ("method_iri", "protocol_iri"),
    "observation_components": ("component_relation_iri",),
}


@dataclass
class PackageData:
    metadata: dict[str, list[dict[str, str]]]
    data_headers: dict[str, list[str]]
    data_rows: dict[str, list[dict[str, str]]]
    descriptor: dict | None


class Validator:
    def __init__(self, package_path: Path) -> None:
        self.package_path = package_path.resolve()
        self.bundle = generate_artifacts.load_schema_bundle()
        self.schemas = self.bundle["metadata_schemas"]
        self.errors: list[str] = []

    def error(self, message: str) -> None:
        self.errors.append(message)

    def validate(self) -> list[str]:
        if not self.package_path.exists():
            return [f"Package path does not exist: {self.package_path}"]
        if not self.package_path.is_dir():
            return [f"Package path is not a directory: {self.package_path}"]

        data = self.load_package()
        self.validate_metadata(data.metadata)
        self.validate_identity_and_joins(data)
        self.validate_descriptor(data)
        return self.errors

    def load_package(self) -> PackageData:
        metadata: dict[str, list[dict[str, str]]] = {}
        for table_name in TABLE_ORDER:
            schema = self.schemas[table_name]
            path = self.package_path / schema["sdp:path"]
            if not path.exists():
                if schema["sdp:requirement"] == "required":
                    self.error(f"Missing required metadata file: {schema['sdp:path']}")
                metadata[table_name] = []
                continue
            metadata[table_name] = self.read_metadata_csv(table_name, path)

        descriptor_path = self.package_path / "datapackage.json"
        descriptor = None
        if descriptor_path.exists():
            try:
                descriptor = json.loads(descriptor_path.read_text(encoding="utf-8"))
            except json.JSONDecodeError as exc:
                self.error(f"datapackage.json is not valid JSON: {exc}")
        else:
            self.error("Missing datapackage.json for strict publication validation.")

        return PackageData(
            metadata=metadata,
            data_headers={},
            data_rows={},
            descriptor=descriptor,
        )

    def read_metadata_csv(self, table_name: str, path: Path) -> list[dict[str, str]]:
        schema = self.schemas[table_name]
        expected_header = [field["name"] for field in schema["fields"]]
        try:
            with path.open("r", encoding="utf-8-sig", newline="") as handle:
                reader = csv.DictReader(handle)
                actual_header = reader.fieldnames or []
                if actual_header != expected_header:
                    self.error(
                        f"{schema['sdp:path']} header must exactly be "
                        f"{expected_header}; found {actual_header}."
                    )
                rows = [
                    {key: normalize_cell(value) for key, value in row.items()}
                    for row in reader
                    if any(not is_blank(value) for value in row.values())
                ]
        except OSError as exc:
            self.error(f"Cannot read {schema['sdp:path']}: {exc}")
            return []

        for row_index, row in enumerate(rows, start=2):
            for field in schema["fields"]:
                value = row.get(field["name"], "")
                location = f"{schema['sdp:path']} row {row_index} field {field['name']}"
                self.validate_field_value(table_name, field, value, location)
        return rows

    def validate_metadata(self, metadata: dict[str, list[dict[str, str]]]) -> None:
        dataset_rows = metadata["dataset"]
        if len(dataset_rows) != 1:
            self.error(
                f"metadata/dataset.csv must contain exactly one dataset row; found {len(dataset_rows)}."
            )

        categorical_columns = [
            row
            for row in metadata["column_dictionary"]
            if row.get("column_role") == "categorical"
        ]
        if categorical_columns and not (self.package_path / "metadata" / "codes.csv").exists():
            self.error(
                "metadata/codes.csv is required because column_dictionary.csv has categorical columns."
            )

        for row_index, row in enumerate(metadata["column_dictionary"], start=2):
            if row.get("column_role") == "measurement":
                for field_name in ("unit_iri", "term_iri", "property_iri", "entity_iri"):
                    if is_blank(row.get(field_name)):
                        self.error(
                            "metadata/column_dictionary.csv row "
                            f"{row_index} measurement column {row.get('column_name', '<blank>')} "
                            f"requires {field_name}."
                        )

        for row_index, row in enumerate(metadata["codes"], start=2):
            if is_blank(row.get("code_value")) and is_blank(row.get("vocabulary_iri")):
                self.error(
                    "metadata/codes.csv row "
                    f"{row_index} requires code_value unless vocabulary_iri is provided."
                )

    def validate_field_value(
        self, table_name: str, field: dict, value: str, location: str
    ) -> None:
        constraints = field.get("constraints", {})
        if constraints.get("required") is True and is_blank(value):
            self.error(f"{location} is required.")
            return
        if is_blank(value):
            return

        if "enum" in constraints and value not in constraints["enum"]:
            self.error(
                f"{location} must be one of {constraints['enum']}; found {value!r}."
            )

        if "pattern" in constraints and re.fullmatch(constraints["pattern"], value) is None:
            self.error(f"{location} must match pattern {constraints['pattern']!r}.")

        if not value_matches_type(value, field["type"]):
            self.error(f"{location} must be a {field['type']} value; found {value!r}.")

        if "minimum" in constraints and field["type"] in {"integer", "number"}:
            try:
                if float(value) < float(constraints["minimum"]):
                    self.error(
                        f"{location} must be at least {constraints['minimum']}; found {value!r}."
                    )
            except ValueError:
                pass

        if field["name"] in ("temporal_start", "temporal_end"):
            self.validate_temporal_value(value, location)

        if field["name"] in IRI_FIELDS.get(table_name, ()):
            values = value.split(";") if field["name"] == "constraint_iri" else [value]
            for iri in values:
                iri = iri.strip()
                if iri and not is_absolute_iri(iri):
                    self.error(f"{location} must be an absolute IRI; found {iri!r}.")

    def validate_temporal_value(self, value: str, location: str) -> None:
        if re.fullmatch(r"\d{4}", value):
            year = int(value)
            if year < 1:
                self.error(f"{location} year must be between 0001 and 9999.")
            return
        try:
            date.fromisoformat(value)
        except ValueError:
            self.error(f"{location} must be a valid YYYY year or YYYY-MM-DD date.")

    def validate_identity_and_joins(self, data: PackageData) -> None:
        metadata = data.metadata
        dataset_ids = [row.get("dataset_id", "") for row in metadata["dataset"]]
        if len(dataset_ids) != len(set(dataset_ids)):
            self.error("metadata/dataset.csv dataset_id values must be unique.")
        dataset_id = dataset_ids[0] if len(dataset_ids) == 1 else None

        tables_by_key: dict[tuple[str, str], dict[str, str]] = {}
        for row_index, row in enumerate(metadata["tables"], start=2):
            key = (row.get("dataset_id", ""), row.get("table_id", ""))
            if dataset_id and row.get("dataset_id") != dataset_id:
                self.error(
                    f"metadata/tables.csv row {row_index} dataset_id does not match dataset.csv."
                )
            if key in tables_by_key:
                self.error(
                    f"metadata/tables.csv row {row_index} duplicates table_id "
                    f"{row.get('table_id')!r} within dataset {row.get('dataset_id')!r}."
                )
            tables_by_key[key] = row

            file_name = row.get("file_name", "")
            target = self.validate_safe_table_path(file_name, f"metadata/tables.csv row {row_index}")
            if target is not None:
                header, rows = read_data_csv(target, self)
                data.data_headers[row.get("table_id", "")] = header
                data.data_rows[row.get("table_id", "")] = rows

        columns_by_table: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
        columns_by_key: dict[tuple[str, str, str], dict[str, str]] = {}
        seen_columns: set[tuple[str, str, str]] = set()
        for row_index, row in enumerate(metadata["column_dictionary"], start=2):
            table_key = (row.get("dataset_id", ""), row.get("table_id", ""))
            if table_key not in tables_by_key:
                self.error(
                    "metadata/column_dictionary.csv row "
                    f"{row_index} references unknown table_id {row.get('table_id')!r}."
                )
            column_key = (
                row.get("dataset_id", ""),
                row.get("table_id", ""),
                row.get("column_name", ""),
            )
            if column_key in seen_columns:
                self.error(
                    "metadata/column_dictionary.csv row "
                    f"{row_index} duplicates column_name {row.get('column_name')!r} "
                    f"within table {row.get('table_id')!r}."
                )
            seen_columns.add(column_key)
            columns_by_table[table_key].append(row)
            columns_by_key[column_key] = row

        self.validate_primary_keys(metadata["tables"], columns_by_table)
        self.validate_data_files(metadata["tables"], columns_by_table, data)
        self.validate_codes(metadata, columns_by_table, data)
        methods_by_key = self.validate_methods(metadata, dataset_id)
        self.validate_observation_structures(
            metadata,
            dataset_id,
            tables_by_key,
            columns_by_key,
            methods_by_key,
            data,
        )

    def validate_methods(
        self,
        metadata: dict[str, list[dict[str, str]]],
        dataset_id: str | None,
    ) -> dict[tuple[str, str], dict[str, str]]:
        methods_by_key: dict[tuple[str, str], dict[str, str]] = {}
        for row_index, method in enumerate(metadata["methods"], start=2):
            if dataset_id and method.get("dataset_id") != dataset_id:
                self.error(
                    f"metadata/methods.csv row {row_index} dataset_id does not match dataset.csv."
                )
            key = (method.get("dataset_id", ""), method.get("method_iri", ""))
            if key in methods_by_key:
                self.error(
                    f"metadata/methods.csv row {row_index} duplicates method_iri "
                    f"{method.get('method_iri')!r} within dataset {method.get('dataset_id')!r}."
                )
            methods_by_key[key] = method

        methods_path = self.package_path / self.schemas["methods"]["sdp:path"]
        static_references = [
            column
            for column in metadata["column_dictionary"]
            if not is_blank(column.get("method_iri"))
        ]
        structures_path = (
            self.package_path
            / self.schemas["observation_structures"]["sdp:path"]
        )
        if (
            static_references
            and structures_path.exists()
            and not methods_path.exists()
        ):
            self.error(
                "A static column_dictionary.method_iri reference used with the "
                "observation-structure extension requires metadata/methods.csv."
            )
        if methods_path.exists():
            for row_index, column in enumerate(metadata["column_dictionary"], start=2):
                method_iri = column.get("method_iri", "")
                if is_blank(method_iri):
                    continue
                key = (column.get("dataset_id", ""), method_iri)
                if key not in methods_by_key:
                    self.error(
                        "metadata/column_dictionary.csv row "
                        f"{row_index} method_iri is not registered in metadata/methods.csv: "
                        f"{method_iri!r}."
                    )
        return methods_by_key

    def validate_observation_structures(
        self,
        metadata: dict[str, list[dict[str, str]]],
        dataset_id: str | None,
        tables_by_key: dict[tuple[str, str], dict[str, str]],
        columns_by_key: dict[tuple[str, str, str], dict[str, str]],
        methods_by_key: dict[tuple[str, str], dict[str, str]],
        data: PackageData,
    ) -> None:
        structures_path = self.package_path / self.schemas["observation_structures"]["sdp:path"]
        components_path = self.package_path / self.schemas["observation_components"]["sdp:path"]
        structures_present = structures_path.exists()
        components_present = components_path.exists()
        if structures_present != components_present:
            self.error(
                "metadata/structure/observation_structures.csv and "
                "metadata/structure/observation_components.csv must be present together."
            )
        if not structures_present or not components_present:
            return

        structures_by_key: dict[tuple[str, str, str], dict[str, str]] = {}
        for row_index, structure in enumerate(metadata["observation_structures"], start=2):
            if dataset_id and structure.get("dataset_id") != dataset_id:
                self.error(
                    "metadata/structure/observation_structures.csv row "
                    f"{row_index} dataset_id does not match dataset.csv."
                )
            table_key = (structure.get("dataset_id", ""), structure.get("table_id", ""))
            if table_key not in tables_by_key:
                self.error(
                    "metadata/structure/observation_structures.csv row "
                    f"{row_index} references unknown table_id {structure.get('table_id')!r}."
                )
            key = table_key + (structure.get("observation_structure_id", ""),)
            if key in structures_by_key:
                self.error(
                    "metadata/structure/observation_structures.csv row "
                    f"{row_index} duplicates observation_structure_id "
                    f"{structure.get('observation_structure_id')!r} within table "
                    f"{structure.get('table_id')!r}."
                )
            structures_by_key[key] = structure

        components_by_structure: dict[
            tuple[str, str, str], list[dict[str, str]]
        ] = defaultdict(list)
        seen_component_orders: set[tuple[str, str, str, str]] = set()
        seen_component_columns: set[tuple[str, str, str, str]] = set()
        for row_index, component in enumerate(metadata["observation_components"], start=2):
            structure_key = (
                component.get("dataset_id", ""),
                component.get("table_id", ""),
                component.get("observation_structure_id", ""),
            )
            if structure_key not in structures_by_key:
                self.error(
                    "metadata/structure/observation_components.csv row "
                    f"{row_index} references unknown observation structure {structure_key!r}."
                )
            column_key = (
                component.get("dataset_id", ""),
                component.get("table_id", ""),
                component.get("column_name", ""),
            )
            if column_key not in columns_by_key:
                self.error(
                    "metadata/structure/observation_components.csv row "
                    f"{row_index} references unknown column {component.get('column_name')!r}."
                )

            order_key = structure_key + (component.get("component_order", ""),)
            if order_key in seen_component_orders:
                self.error(
                    "metadata/structure/observation_components.csv row "
                    f"{row_index} duplicates component_order within {structure_key!r}."
                )
            seen_component_orders.add(order_key)

            bound_column_key = structure_key + (component.get("column_name", ""),)
            if bound_column_key in seen_component_columns:
                self.error(
                    "metadata/structure/observation_components.csv row "
                    f"{row_index} binds column {component.get('column_name')!r} more than once."
                )
            seen_component_columns.add(bound_column_key)
            components_by_structure[structure_key].append(component)

        measure_bindings: dict[tuple[str, str, str], tuple[str, str, str]] = {}
        for structure_key in structures_by_key:
            components = components_by_structure.get(structure_key, [])
            measure_components = [
                component
                for component in components
                if component.get("component_role") == "measure"
            ]
            if len(measure_components) != 1:
                self.error(
                    f"Observation structure {structure_key!r} must have exactly one measure component; "
                    f"found {len(measure_components)}."
                )
            dimension_count = sum(
                component.get("component_role") == "dimension"
                for component in components
            )
            if dimension_count < 1:
                self.error(
                    f"Observation structure {structure_key!r} must have at least one "
                    "dimension component."
                )

            orders = sorted(
                int(component["component_order"])
                for component in components
                if re.fullmatch(r"[+-]?\d+", component.get("component_order", ""))
            )
            if orders != list(range(1, len(components) + 1)):
                self.error(
                    f"Observation structure {structure_key!r} component_order values must be "
                    f"contiguous from 1; found {orders}."
                )

            for component in components:
                role = component.get("component_role")
                column_key = structure_key[:2] + (component.get("column_name", ""),)
                column = columns_by_key.get(column_key)
                if role == "measure":
                    if column is not None and column.get("column_role") != "measurement":
                        self.error(
                            f"Observation structure {structure_key!r} measure component "
                            f"{component.get('column_name')!r} must bind a measurement column."
                        )
                    if column_key in measure_bindings:
                        self.error(
                            f"Measurement column {column_key!r} is bound as the measure of more "
                            "than one observation structure."
                        )
                    measure_bindings[column_key] = structure_key
                if role in {"measure", "dimension"} and parse_bool(
                    component.get("required_when_observed")
                ) is not True:
                    self.error(
                        f"Observation structure {structure_key!r} {role} component "
                        f"{component.get('column_name')!r} must set required_when_observed to TRUE."
                    )
                if component.get("component_relation_iri") == SOSA_USED_PROCEDURE:
                    if role != "attribute":
                        self.error(
                            f"Observation structure {structure_key!r} sosa:usedProcedure "
                            "component must have component_role attribute."
                        )
                    if column is not None and column.get("column_role") != "categorical":
                        self.error(
                            f"Observation structure {structure_key!r} sosa:usedProcedure "
                            "component must bind a categorical column."
                        )

            if len(measure_components) == 1:
                self.validate_structure_data(
                    structure_key,
                    components,
                    measure_components[0],
                    metadata,
                    columns_by_key,
                    methods_by_key,
                    data,
                )

        measurement_columns = {
            key
            for key, column in columns_by_key.items()
            if column.get("column_role") == "measurement"
        }
        missing_measurements = sorted(measurement_columns - set(measure_bindings))
        if missing_measurements:
            self.error(
                "When observation structures are present, every measurement column "
                "must be bound as exactly one measure; missing "
                f"{missing_measurements!r}."
            )

    def validate_structure_data(
        self,
        structure_key: tuple[str, str, str],
        components: list[dict[str, str]],
        measure_component: dict[str, str],
        metadata: dict[str, list[dict[str, str]]],
        columns_by_key: dict[tuple[str, str, str], dict[str, str]],
        methods_by_key: dict[tuple[str, str], dict[str, str]],
        data: PackageData,
    ) -> None:
        table_id = structure_key[1]
        measure_name = measure_component.get("column_name", "")
        dimensions = [
            component
            for component in components
            if component.get("component_role") == "dimension"
        ]
        attributes = [
            component
            for component in components
            if component.get("component_role") == "attribute"
        ]
        invariant_components = [measure_component, *attributes]
        values_by_dimensions: dict[tuple[str, ...], tuple[str, ...]] = {}

        codes_by_key = {
            (
                code.get("dataset_id", ""),
                code.get("table_id", ""),
                code.get("column_name", ""),
                code.get("code_value", ""),
            ): code
            for code in metadata["codes"]
            if not is_blank(code.get("code_value"))
        }
        procedure_attributes = [
            component
            for component in attributes
            if component.get("component_relation_iri") == SOSA_USED_PROCEDURE
        ]
        reported_procedure_codes: set[tuple[str, str]] = set()

        # A code list declares the complete allowed procedure domain. Validate
        # every enumerated value, even if this particular data version does not
        # use it, so a future row cannot activate an unregistered procedure.
        for procedure_component in procedure_attributes:
            column_name = procedure_component.get("column_name", "")
            procedure_codes = [
                code
                for code in metadata["codes"]
                if code.get("dataset_id", "") == structure_key[0]
                and code.get("table_id", "") == structure_key[1]
                and code.get("column_name", "") == column_name
                and not is_blank(code.get("code_value"))
            ]
            for code in procedure_codes:
                code_value = normalize_cell(code.get("code_value"))
                method_iri = normalize_cell(code.get("term_iri"))
                if is_blank(method_iri):
                    self.error(
                        f"Observation structure {structure_key!r} sosa:usedProcedure code "
                        f"{code_value!r} in column {column_name!r} requires a term_iri in "
                        "metadata/codes.csv."
                    )
                elif (structure_key[0], method_iri) not in methods_by_key:
                    self.error(
                        f"Observation structure {structure_key!r} sosa:usedProcedure code "
                        f"{code_value!r} term_iri is not registered in metadata/methods.csv: "
                        f"{method_iri!r}."
                    )

        component_columns = {
            component.get("column_name", ""): columns_by_key.get(
                structure_key[:2] + (component.get("column_name", ""),),
                {},
            )
            for component in components
        }

        for row_index, row in enumerate(data.data_rows.get(table_id, []), start=2):
            measure_value = normalize_cell(row.get(measure_name, ""))
            if is_blank(measure_value):
                continue

            for component in components:
                if parse_bool(component.get("required_when_observed")) is True:
                    column_name = component.get("column_name", "")
                    if is_blank(row.get(column_name)):
                        self.error(
                            f"{table_id} row {row_index} observation structure "
                            f"{structure_key[2]!r} component {column_name!r} is empty but "
                            "required_when_observed is TRUE."
                        )

            dimension_values = tuple(
                normalize_typed_cell(
                    row.get(component.get("column_name", ""), ""),
                    component_columns[component.get("column_name", "")].get(
                        "value_type", "string"
                    ),
                )
                for component in dimensions
            )
            if all(not is_blank(value) for value in dimension_values):
                invariant_values = tuple(
                    normalize_typed_cell(
                        row.get(component.get("column_name", ""), ""),
                        component_columns[component.get("column_name", "")].get(
                            "value_type", "string"
                        ),
                    )
                    for component in invariant_components
                )
                previous = values_by_dimensions.get(dimension_values)
                if previous is not None and previous != invariant_values:
                    self.error(
                        f"Observation structure {structure_key!r} has conflicting values at "
                        f"dimension tuple {dimension_values!r}: {previous!r} and "
                        f"{invariant_values!r}."
                    )
                else:
                    values_by_dimensions[dimension_values] = invariant_values

            for procedure_component in procedure_attributes:
                column_name = procedure_component.get("column_name", "")
                code_value = normalize_cell(row.get(column_name, ""))
                if is_blank(code_value):
                    continue
                report_key = (column_name, code_value)
                if report_key in reported_procedure_codes:
                    continue
                reported_procedure_codes.add(report_key)
                code_key = structure_key[:2] + (column_name, code_value)
                code = codes_by_key.get(code_key, {})
                method_iri = normalize_cell(code.get("term_iri"))
                if is_blank(method_iri):
                    self.error(
                        f"Observation structure {structure_key!r} sosa:usedProcedure code "
                        f"{code_value!r} in column {column_name!r} requires a term_iri in "
                        "metadata/codes.csv."
                    )
                elif (structure_key[0], method_iri) not in methods_by_key:
                    self.error(
                        f"Observation structure {structure_key!r} sosa:usedProcedure code "
                        f"{code_value!r} term_iri is not registered in metadata/methods.csv: "
                        f"{method_iri!r}."
                    )

    def validate_safe_table_path(self, file_name: str, location: str) -> Path | None:
        if is_blank(file_name):
            self.error(f"{location} file_name is required.")
            return None
        if "://" in file_name or file_name.startswith("//"):
            self.error(f"{location} file_name must not be a URL: {file_name!r}.")
            return None
        if "\\" in file_name:
            self.error(f"{location} file_name must use forward slashes, not backslashes.")
            return None
        if re.match(r"^[A-Za-z]:", file_name):
            self.error(f"{location} file_name must not be a Windows drive path.")
            return None

        posix_path = PurePosixPath(file_name)
        if posix_path.is_absolute() or ".." in posix_path.parts:
            self.error(f"{location} file_name must be a safe relative path: {file_name!r}.")
            return None

        target = self.package_path / Path(*posix_path.parts)
        if not target.exists():
            self.error(f"{location} file_name points to missing file: {file_name!r}.")
            return None
        try:
            target_real = target.resolve(strict=True)
            target_real.relative_to(self.package_path)
        except (OSError, ValueError):
            self.error(f"{location} file_name escapes the package root: {file_name!r}.")
            return None
        if not target.is_file():
            self.error(f"{location} file_name must point to a file: {file_name!r}.")
            return None
        return target

    def validate_primary_keys(
        self,
        table_rows: list[dict[str, str]],
        columns_by_table: dict[tuple[str, str], list[dict[str, str]]],
    ) -> None:
        for row_index, table in enumerate(table_rows, start=2):
            primary_key = table.get("primary_key", "")
            if is_blank(primary_key):
                continue
            if ", " in primary_key or " ," in primary_key:
                self.error(
                    f"metadata/tables.csv row {row_index} primary_key must be comma-separated with no spaces."
                )
            column_names = {
                column["column_name"]
                for column in columns_by_table[(table.get("dataset_id", ""), table.get("table_id", ""))]
            }
            for key_part in [part.strip() for part in primary_key.split(",") if part.strip()]:
                if key_part not in column_names:
                    self.error(
                        f"metadata/tables.csv row {row_index} primary_key references missing column {key_part!r}."
                    )

    def validate_data_files(
        self,
        table_rows: list[dict[str, str]],
        columns_by_table: dict[tuple[str, str], list[dict[str, str]]],
        data: PackageData,
    ) -> None:
        for table in table_rows:
            table_id = table.get("table_id", "")
            table_key = (table.get("dataset_id", ""), table_id)
            dictionary_rows = columns_by_table[table_key]
            expected_header = [row["column_name"] for row in dictionary_rows]
            actual_header = data.data_headers.get(table_id, [])
            if actual_header != expected_header:
                self.error(
                    f"{table.get('file_name')} header must exactly match "
                    "metadata/column_dictionary.csv rows for table "
                    f"{table_id!r}; expected {expected_header}, found {actual_header}."
                )

            for data_index, data_row in enumerate(data.data_rows.get(table_id, []), start=2):
                for column in dictionary_rows:
                    column_name = column["column_name"]
                    value = normalize_cell(data_row.get(column_name, ""))
                    location = f"{table.get('file_name')} row {data_index} field {column_name}"
                    if parse_bool(column.get("required")) is True and is_blank(value):
                        self.error(f"{location} is required by column_dictionary.csv.")
                        continue
                    if not is_blank(value) and not value_matches_type(
                        value, column.get("value_type", "string")
                    ):
                        self.error(
                            f"{location} must be a {column.get('value_type')} value; found {value!r}."
                        )

    def validate_codes(
        self,
        metadata: dict[str, list[dict[str, str]]],
        columns_by_table: dict[tuple[str, str], list[dict[str, str]]],
        data: PackageData,
    ) -> None:
        categorical_columns = {
            (row.get("dataset_id", ""), row.get("table_id", ""), row.get("column_name", ""))
            for row in metadata["column_dictionary"]
            if row.get("column_role") == "categorical"
        }

        code_rows_by_key: dict[tuple[str, str, str, str], dict[str, str]] = {}
        conflict_fields = (
            "code_label",
            "code_description",
            "vocabulary_iri",
            "term_iri",
            "term_type",
        )
        for row_index, code in enumerate(metadata["codes"], start=2):
            column_key = (
                code.get("dataset_id", ""),
                code.get("table_id", ""),
                code.get("column_name", ""),
            )
            if column_key not in categorical_columns:
                self.error(
                    f"metadata/codes.csv row {row_index} targets a non-categorical or unknown column: "
                    f"{column_key!r}."
                )
            code_key = column_key + (code.get("code_value", ""),)
            if code_key in code_rows_by_key:
                existing = code_rows_by_key[code_key]
                differing = [
                    field
                    for field in conflict_fields
                    if normalize_cell(existing.get(field)) != normalize_cell(code.get(field))
                ]
                if differing:
                    self.error(
                        f"metadata/codes.csv row {row_index} conflicts with another row for "
                        f"{code_key!r} on {', '.join(differing)}."
                    )
            else:
                code_rows_by_key[code_key] = code

        for table_key, dictionary_rows in columns_by_table.items():
            table_id = table_key[1]
            categorical_names = [
                row["column_name"]
                for row in dictionary_rows
                if row.get("column_role") == "categorical"
            ]
            for data_index, data_row in enumerate(data.data_rows.get(table_id, []), start=2):
                for column_name in categorical_names:
                    observed = normalize_cell(data_row.get(column_name, ""))
                    if is_blank(observed):
                        continue
                    code_key = table_key + (column_name, observed)
                    if code_key not in code_rows_by_key:
                        self.error(
                            f"{table_id} row {data_index} field {column_name} observed value "
                            f"{observed!r} has no matching metadata/codes.csv code_value."
                        )

    def validate_descriptor(self, data: PackageData) -> None:
        descriptor = data.descriptor
        if descriptor is None:
            return

        expected_profile = generate_artifacts.render_profile(self.bundle)
        validator = jsonschema.Draft7Validator(expected_profile)
        for error in sorted(validator.iter_errors(descriptor), key=str):
            self.error(f"datapackage.json profile validation: {error.message}")

        if descriptor.get("profile") != PROFILE_URL:
            self.error(f"datapackage.json profile must be {PROFILE_URL}.")

        metadata = data.metadata
        dataset = metadata["dataset"][0] if len(metadata["dataset"]) == 1 else {}
        if dataset:
            descriptor_checks = {
                "id": "dataset_id",
                "title": "title",
                "description": "description",
            }
            for descriptor_field, csv_field in descriptor_checks.items():
                if normalize_cell(descriptor.get(descriptor_field)) != normalize_cell(dataset.get(csv_field)):
                    self.error(
                        f"datapackage.json {descriptor_field} must match "
                        f"metadata/dataset.csv {csv_field}."
                    )
            self.validate_descriptor_license(descriptor, dataset)
            self.validate_descriptor_contributors(descriptor, dataset)

        resources = descriptor.get("resources", [])
        if not isinstance(resources, list):
            self.error("datapackage.json resources must be an array.")
            return
        resources_by_path = {
            resource.get("path"): resource
            for resource in resources
            if isinstance(resource, dict) and isinstance(resource.get("path"), str)
        }

        self.validate_descriptor_metadata_resources(resources_by_path)
        self.validate_descriptor_data_resources(resources_by_path, data)

    def validate_descriptor_license(self, descriptor: dict, dataset: dict[str, str]) -> None:
        license_text = dataset.get("license", "")
        expected = KNOWN_LICENSES.get(license_text)
        if expected is None:
            self.error(
                "metadata/dataset.csv license must be a known publication license "
                f"({', '.join(sorted(KNOWN_LICENSES))}); found {license_text!r}."
            )
            return
        licenses = descriptor.get("licenses")
        if not isinstance(licenses, list) or not licenses:
            self.error("datapackage.json licenses must include the dataset license.")
            return
        if not any(
            all(resource_license.get(key) == value for key, value in expected.items())
            for resource_license in licenses
            if isinstance(resource_license, dict)
        ):
            self.error(
                "datapackage.json licenses must map "
                f"{license_text!r} to name={expected['name']!r}, "
                f"title={expected['title']!r}, and path={expected['path']!r}."
            )

    def validate_descriptor_contributors(self, descriptor: dict, dataset: dict[str, str]) -> None:
        contributors = descriptor.get("contributors")
        if not isinstance(contributors, list):
            self.error("datapackage.json contributors must be an array.")
            return
        if not any(
            contributor.get("role") == "creator"
            and contributor.get("title") == dataset.get("creator")
            for contributor in contributors
            if isinstance(contributor, dict)
        ):
            self.error("datapackage.json contributors must include the dataset creator.")
        if not any(
            contributor.get("role") == "contact"
            and contributor.get("title") == dataset.get("contact_name")
            and contributor.get("email") == dataset.get("contact_email")
            for contributor in contributors
            if isinstance(contributor, dict)
        ):
            self.error("datapackage.json contributors must include the dataset contact.")

    def validate_descriptor_metadata_resources(self, resources_by_path: dict[str, dict]) -> None:
        for table_name in TABLE_ORDER:
            schema = self.schemas[table_name]
            path = schema["sdp:path"]
            if (
                schema["sdp:requirement"] != "required"
                and not (self.package_path / path).exists()
            ):
                continue
            expected = generate_artifacts.metadata_resource(table_name, schema)
            resource = resources_by_path.get(path)
            if resource is None:
                self.error(f"datapackage.json resources must include {path}.")
                continue
            for field in ("name", "path", "profile", "schema"):
                if resource.get(field) != expected[field]:
                    self.error(
                        f"datapackage.json resource {path} field {field} must be "
                        f"{expected[field]!r}; found {resource.get(field)!r}."
                    )

    def validate_descriptor_data_resources(
        self, resources_by_path: dict[str, dict], data: PackageData
    ) -> None:
        metadata = data.metadata
        columns_by_table: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
        for column in metadata["column_dictionary"]:
            columns_by_table[(column.get("dataset_id", ""), column.get("table_id", ""))].append(column)

        for table in metadata["tables"]:
            path = table.get("file_name", "")
            resource = resources_by_path.get(path)
            if resource is None:
                self.error(f"datapackage.json resources must include data resource {path}.")
                continue
            if resource.get("profile") != "tabular-data-resource":
                self.error(f"datapackage.json resource {path} must use tabular-data-resource.")
            schema = resource.get("schema")
            if not isinstance(schema, dict):
                self.error(f"datapackage.json resource {path} must include an inline schema.")
                continue

            expected_primary_key = descriptor_primary_key(table.get("primary_key", ""))
            if expected_primary_key and schema.get("primaryKey") != expected_primary_key:
                self.error(
                    f"datapackage.json resource {path} primaryKey must be {expected_primary_key!r}; "
                    f"found {schema.get('primaryKey')!r}."
                )

            fields = schema.get("fields")
            if not isinstance(fields, list):
                self.error(f"datapackage.json resource {path} schema.fields must be an array.")
                continue
            expected_fields = [
                descriptor_field_from_column(column)
                for column in columns_by_table[(table.get("dataset_id", ""), table.get("table_id", ""))]
            ]
            if fields != expected_fields:
                self.error(
                    f"datapackage.json resource {path} schema.fields must match "
                    "metadata/column_dictionary.csv-derived fields."
                )


def normalize_cell(value: object) -> str:
    if value is None:
        return ""
    return str(value).strip()


def normalize_typed_cell(value: object, field_type: str) -> str:
    """Canonicalize already validated values for semantic equality checks."""
    text = normalize_cell(value)
    if text == "":
        return ""
    if field_type == "integer":
        return str(int(text))
    if field_type == "number":
        try:
            number = Decimal(text)
        except InvalidOperation:
            return text
        if number == 0:
            return "0"
        return format(number.normalize(), "f")
    if field_type == "boolean":
        return "true" if parse_bool(text) is True else "false"
    if field_type == "date":
        try:
            return date.fromisoformat(text).isoformat()
        except ValueError:
            return text
    if field_type == "datetime":
        candidate = text[:-1] + "+00:00" if text.endswith("Z") else text
        try:
            parsed = datetime.fromisoformat(candidate)
        except ValueError:
            return text
        if parsed.tzinfo is not None:
            parsed = parsed.astimezone(timezone.utc)
        return parsed.isoformat()
    if field_type == "year":
        return f"{int(text):04d}"
    return text


def is_blank(value: object) -> bool:
    return normalize_cell(value) == ""


def parse_bool(value: object) -> bool | None:
    normalized = normalize_cell(value).lower()
    if normalized in {"true", "1", "yes"}:
        return True
    if normalized in {"false", "0", "no", ""}:
        return False
    return None


def value_matches_type(value: str, field_type: str) -> bool:
    if field_type == "string":
        return True
    if field_type == "integer":
        return re.fullmatch(r"[+-]?\d+", value) is not None
    if field_type == "number":
        try:
            float(value)
        except ValueError:
            return False
        return True
    if field_type == "boolean":
        return parse_bool(value) is not None
    if field_type == "date":
        try:
            date.fromisoformat(value)
        except ValueError:
            return False
        return True
    if field_type == "datetime":
        candidate = value[:-1] + "+00:00" if value.endswith("Z") else value
        try:
            datetime.fromisoformat(candidate)
        except ValueError:
            return False
        return True
    if field_type == "year":
        return re.fullmatch(r"\d{4}", value) is not None
    return False


def is_absolute_iri(value: str) -> bool:
    if any(char.isspace() for char in value):
        return False
    parsed = urlparse(value)
    if not parsed.scheme:
        return False
    if parsed.scheme in {"http", "https"} and not parsed.netloc:
        return False
    return True


def read_data_csv(path: Path, validator: Validator) -> tuple[list[str], list[dict[str, str]]]:
    try:
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            rows = [
                {key: normalize_cell(value) for key, value in row.items()}
                for row in reader
                if any(not is_blank(value) for value in row.values())
            ]
            return reader.fieldnames or [], rows
    except OSError as exc:
        validator.error(f"Cannot read data file {path.relative_to(validator.package_path)}: {exc}")
        return [], []


def descriptor_primary_key(primary_key: str) -> str | list[str] | None:
    if is_blank(primary_key):
        return None
    parts = [part.strip() for part in primary_key.split(",") if part.strip()]
    if len(parts) == 1:
        return parts[0]
    return parts


def descriptor_field_from_column(column: dict[str, str]) -> dict:
    field = {
        "name": column.get("column_name", ""),
        "title": column.get("column_label", ""),
        "description": column.get("column_description", ""),
        "type": column.get("value_type", "string"),
    }
    if parse_bool(column.get("required")) is True:
        field["constraints"] = {"required": True}
    return field


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("package_path", help="Path to an SDP package directory")
    args = parser.parse_args(argv)

    validator = Validator(Path(args.package_path))
    errors = validator.validate()
    if errors:
        print(f"Strict SDP validation failed for {args.package_path}:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1

    print(f"Strict SDP validation passed: {args.package_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
