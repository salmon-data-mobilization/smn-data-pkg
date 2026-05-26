#!/usr/bin/env python3
"""Generate SDP template artifacts from Frictionless schema sources."""

from __future__ import annotations

import argparse
import csv
import difflib
import filecmp
import json
import os
import shutil
import sys
import tempfile
import zipfile
from pathlib import Path

try:
    import yaml
except ImportError:  # pragma: no cover - exercised by users without PyYAML
    yaml = None


ROOT = Path(__file__).resolve().parents[1]
METADATA_SCHEMA_DIR = ROOT / "schema" / "frictionless" / "metadata"
PROFILE_SOURCE_PATH = ROOT / "schema" / "frictionless" / "profile-source.json"
RULES_PATH = ROOT / "schema" / "sdp.rules.yaml"
PROFILE_PATH = ROOT / "profiles" / "salmon-data-package" / "v0.2" / "profile.json"
TEMPLATE_SOURCE_DIR = ROOT / "template-source" / "salmon-data-package-template"
TEMPLATE_DIR = ROOT / "templates" / "salmon-data-package-template"
ZIP_PATH = ROOT / "templates" / "salmon-data-package-template.zip"
FIELD_REFERENCE_PATH = ROOT / "docs" / "field-reference.md"
PROFILE_URL = (
    "https://dfo-pacific-science.github.io/smn-data-pkg/"
    "profiles/salmon-data-package/v0.2/profile.json"
)
TABLE_ORDER = ("dataset", "tables", "column_dictionary", "codes")
FRICTIONLESS_TYPES = {
    "string",
    "integer",
    "number",
    "boolean",
    "date",
    "datetime",
    "year",
}
REQUIREMENTS = {"required", "optional", "recommended", "conditional"}
ZIP_TIMESTAMP = (2024, 1, 1, 0, 0, 0)


def repo_path(root: Path, path: Path) -> Path:
    return root / path.relative_to(ROOT)


def read_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def load_rules(path: Path = RULES_PATH) -> dict:
    if yaml is None:
        raise SystemExit(
            "PyYAML is required for schema/sdp.rules.yaml. "
            "Install it with `python3 -m pip install PyYAML`."
        )
    with path.open("r", encoding="utf-8") as handle:
        rules = yaml.safe_load(handle)
    if not isinstance(rules, dict) or not isinstance(rules.get("rules"), list):
        raise ValueError("schema/sdp.rules.yaml must define a rules list.")
    return rules


def load_schema_bundle(root: Path = ROOT) -> dict:
    metadata_schemas = {
        table_name: read_json(
            repo_path(root, METADATA_SCHEMA_DIR) / f"{table_name}.schema.json"
        )
        for table_name in TABLE_ORDER
    }
    bundle = {
        "metadata_schemas": metadata_schemas,
        "profile_source": read_json(repo_path(root, PROFILE_SOURCE_PATH)),
        "rules": load_rules(repo_path(root, RULES_PATH)),
    }
    validate_schema_bundle(bundle)
    return bundle


def validate_schema_bundle(bundle: dict) -> None:
    profile_source = bundle["profile_source"]
    for key in ("$schema", "title", "description"):
        if key not in profile_source:
            raise ValueError(f"profile-source.json is missing {key}.")

    profile = render_profile(bundle)
    if profile.get("$id") != PROFILE_URL:
        raise ValueError(f"Profile $id must be {PROFILE_URL}.")
    profile_const = (
        profile.get("properties", {})
        .get("profile", {})
        .get("const")
    )
    if profile_const != PROFILE_URL:
        raise ValueError(f"Profile schema must require profile {PROFILE_URL}.")

    rules = bundle["rules"]
    if rules.get("profile") != PROFILE_URL:
        raise ValueError("schema/sdp.rules.yaml profile does not match profile.json.")
    if not rules.get("version"):
        raise ValueError("schema/sdp.rules.yaml must include version.")

    for table_name in TABLE_ORDER:
        schema = bundle["metadata_schemas"][table_name]
        if schema.get("sdp:table") != table_name:
            raise ValueError(f"{table_name}.schema.json has incorrect sdp:table.")
        if schema.get("sdp:requirement") not in REQUIREMENTS:
            raise ValueError(f"{table_name}.schema.json has invalid sdp:requirement.")
        if not schema.get("sdp:path", "").startswith("metadata/"):
            raise ValueError(f"{table_name}.schema.json sdp:path must be under metadata/.")

        fields = schema.get("fields")
        if not isinstance(fields, list) or not fields:
            raise ValueError(f"{table_name}.schema.json must define fields.")

        names = []
        for field in fields:
            for key in ("name", "type", "description"):
                if key not in field:
                    raise ValueError(f"{table_name} field is missing {key}.")
            if field["type"] not in FRICTIONLESS_TYPES:
                raise ValueError(f"{table_name}.{field['name']} has invalid type.")
            requirement = field_requirement(field)
            if requirement not in REQUIREMENTS:
                raise ValueError(f"{table_name}.{field['name']} has invalid requirement.")
            constraints = field.get("constraints", {})
            if "enum" in constraints and not isinstance(constraints["enum"], list):
                raise ValueError(f"{table_name}.{field['name']} constraints.enum must be a list.")
            names.append(field["name"])

        duplicates = sorted({name for name in names if names.count(name) > 1})
        if duplicates:
            raise ValueError(
                f"{table_name}.schema.json has duplicate fields: {', '.join(duplicates)}"
            )


def metadata_schema_url(schema: dict) -> str:
    return (
        "https://dfo-pacific-science.github.io/smn-data-pkg/"
        f"schema/frictionless/metadata/{schema['sdp:table']}.schema.json"
    )


def metadata_resource_name(table_name: str) -> str:
    if table_name == "column_dictionary":
        return "sdp_column_dictionary"
    return f"sdp_{table_name}"


def metadata_resource(table_name: str, schema: dict) -> dict:
    resource = {
        "name": metadata_resource_name(table_name),
        "path": schema["sdp:path"],
        "profile": "tabular-data-resource",
        "title": schema["title"].removesuffix(" schema"),
        "description": schema["description"],
        "schema": metadata_schema_url(schema),
        "sdp:requirement": schema["sdp:requirement"],
    }
    if schema.get("sdp:condition"):
        resource["sdp:condition"] = schema["sdp:condition"]
    return resource


def required_metadata_resource_clause(resource: dict) -> dict:
    return {
        "properties": {
            "resources": {
                "contains": {
                    "type": "object",
                    "required": ["name", "path", "profile", "schema"],
                    "properties": {
                        "name": {"const": resource["name"]},
                        "path": {"const": resource["path"]},
                        "profile": {"const": "tabular-data-resource"},
                        "schema": {"const": resource["schema"]},
                    },
                }
            }
        }
    }


def render_profile(bundle: dict) -> dict:
    profile_source = bundle["profile_source"]
    metadata_resources = [
        metadata_resource(table_name, bundle["metadata_schemas"][table_name])
        for table_name in TABLE_ORDER
    ]
    required_resources = [
        resource
        for resource in metadata_resources
        if resource["sdp:requirement"] == "required"
    ]
    profile = {
        "$schema": profile_source["$schema"],
        "$id": PROFILE_URL,
        "title": profile_source["title"],
        "description": profile_source["description"],
        "type": "object",
        "required": ["profile", "resources"],
        "properties": {
            "profile": {"const": PROFILE_URL},
            "resources": {
                "type": "array",
                "minItems": len(required_resources) + 1,
                "items": {
                    "type": "object",
                    "required": ["name", "path", "profile", "schema"],
                    "properties": {
                        "name": {"type": "string"},
                        "path": {"type": "string"},
                        "profile": {"const": "tabular-data-resource"},
                        "schema": {},
                    },
                },
            },
        },
        "allOf": [
            required_metadata_resource_clause(resource)
            for resource in required_resources
        ],
        "sdp:version": bundle["rules"]["version"],
        "sdp:metadataResources": metadata_resources,
        "sdp:rules": (
            "https://dfo-pacific-science.github.io/smn-data-pkg/"
            "schema/sdp.rules.yaml"
        ),
    }
    return profile


def field_requirement(field: dict) -> str:
    if field.get("constraints", {}).get("required") is True:
        return "required"
    return field.get("sdp:requirement", "optional")


def field_allowed_values(field: dict) -> list[str]:
    return field.get("constraints", {}).get("enum", [])


def field_examples(field: dict) -> list[str]:
    examples = field.get("sdp:examples")
    if isinstance(examples, list):
        return examples
    example = field.get("example")
    return [example] if example else []


def render_template_readme(root: Path = ROOT) -> str:
    source_path = repo_path(root, TEMPLATE_SOURCE_DIR) / "README.md"
    if not source_path.exists():
        raise FileNotFoundError(
            f"Template README source is missing: {source_path}. "
            "Create template-source/salmon-data-package-template/README.md."
        )

    content = source_path.read_text(encoding="utf-8")
    if "{{" in content or "}}" in content:
        raise ValueError(
            "Template README source is plain Markdown; placeholders are not supported."
        )
    return content


def render_data_readme() -> str:
    return """# Data Files

Place the data CSV files for this package in this directory.

Each file listed here must be referenced by a row in `../metadata/tables.csv`.
"""


def render_field_reference(bundle: dict) -> str:
    lines = [
        "# SDP Field Reference",
        "",
        "<!-- Generated by scripts/generate_artifacts.py; do not edit by hand. -->",
        "",
        f"SDP version: `{bundle['rules']['version']}`",
        "",
        "This non-normative reference is generated from the Frictionless Table Schema files in `schema/frictionless/metadata/`. `SPECIFICATION.md` remains the human-readable validity specification.",
        "",
    ]

    for table_name in TABLE_ORDER:
        schema = bundle["metadata_schemas"][table_name]
        lines.extend(
            [
                f"## `{schema['sdp:path']}`",
                "",
                schema.get("description", ""),
                "",
                f"Requirement: `{schema['sdp:requirement']}`",
                "",
            ]
        )
        if schema.get("sdp:condition"):
            lines.extend([f"Condition: {schema['sdp:condition']}", ""])
        if schema.get("sdp:rowRule"):
            lines.extend([schema["sdp:rowRule"], ""])

        lines.extend(
            [
                "| Column | Type | Requirement | Description | Notes |",
                "| --- | --- | --- | --- | --- |",
            ]
        )
        for field in schema["fields"]:
            notes = []
            if field.get("sdp:condition"):
                notes.append(field["sdp:condition"])
            allowed_values = field_allowed_values(field)
            if allowed_values:
                notes.append("Allowed: " + ", ".join(f"`{v}`" for v in allowed_values))
            examples = field_examples(field)
            if examples:
                notes.append("Examples: " + ", ".join(f"`{v}`" for v in examples))
            lines.append(
                "| {name} | {type} | {requirement} | {description} | {notes} |".format(
                    name=field["name"],
                    type=field["type"],
                    requirement=field_requirement(field),
                    description=field["description"].replace("|", "\\|"),
                    notes="<br>".join(notes).replace("|", "\\|"),
                )
            )
        lines.append("")

    return "\n".join(lines)


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8", newline="\n")


def write_csv_header(path: Path, fields: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow([field["name"] for field in fields])


def create_deterministic_zip(source_dir: Path, zip_path: Path) -> None:
    zip_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(source_dir.rglob("*")):
            if path.is_dir():
                continue
            rel = path.relative_to(source_dir.parent)
            info = zipfile.ZipInfo(str(rel).replace(os.sep, "/"), ZIP_TIMESTAMP)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            archive.writestr(info, path.read_bytes())


def generate(bundle: dict, root: Path = ROOT) -> None:
    template_dir = repo_path(root, TEMPLATE_DIR)
    field_reference_path = repo_path(root, FIELD_REFERENCE_PATH)
    zip_path = repo_path(root, ZIP_PATH)
    profile_path = repo_path(root, PROFILE_PATH)

    if template_dir.exists():
        shutil.rmtree(template_dir)

    write_text(
        profile_path,
        json.dumps(render_profile(bundle), indent=2, ensure_ascii=False) + "\n",
    )
    write_text(template_dir / "README.md", render_template_readme(root=root))
    write_text(template_dir / "data" / "README.md", render_data_readme())

    for table_name in TABLE_ORDER:
        schema = bundle["metadata_schemas"][table_name]
        target = template_dir / schema["sdp:path"]
        write_csv_header(target, schema["fields"])

    write_text(field_reference_path, render_field_reference(bundle))
    create_deterministic_zip(template_dir, zip_path)


def dircmp_diffs(left: Path, right: Path) -> list[str]:
    diffs: list[str] = []
    comparison = filecmp.dircmp(left, right)
    for name in comparison.left_only:
        diffs.append(f"Only in generated artifacts: {left / name}")
    for name in comparison.right_only:
        diffs.append(f"Only in repository artifacts: {right / name}")
    for name in comparison.diff_files:
        left_file = left / name
        right_file = right / name
        if left_file.suffix in {".csv", ".md", ".yaml", ".yml", ".json", ".txt"}:
            left_lines = left_file.read_text(encoding="utf-8").splitlines(True)
            right_lines = right_file.read_text(encoding="utf-8").splitlines(True)
            diffs.extend(
                difflib.unified_diff(
                    right_lines,
                    left_lines,
                    fromfile=str(right_file),
                    tofile=str(left_file),
                )
            )
        else:
            diffs.append(f"Binary files differ: {right_file}")
    for subdir in comparison.common_dirs:
        diffs.extend(dircmp_diffs(left / subdir, right / subdir))
    return diffs


def check() -> int:
    with tempfile.TemporaryDirectory() as temp:
        temp_root = Path(temp)
        shutil.copytree(ROOT / "schema", temp_root / "schema")
        template_source_root = ROOT / "template-source"
        if not template_source_root.exists():
            raise FileNotFoundError(
                "Template source directory is missing: template-source/"
            )
        shutil.copytree(template_source_root, temp_root / "template-source")
        (temp_root / "docs").mkdir()
        (temp_root / "profiles").mkdir()
        (temp_root / "templates").mkdir()

        bundle = load_schema_bundle(root=temp_root)
        generate(bundle, root=temp_root)

        diffs = []
        diffs.extend(dircmp_diffs(temp_root / "profiles", ROOT / "profiles"))
        diffs.extend(dircmp_diffs(temp_root / "templates", ROOT / "templates"))

        generated_ref = temp_root / FIELD_REFERENCE_PATH.relative_to(ROOT)
        repo_ref = FIELD_REFERENCE_PATH
        if not repo_ref.exists():
            diffs.append(f"Missing generated artifact: {repo_ref}")
        elif generated_ref.read_text(encoding="utf-8") != repo_ref.read_text(encoding="utf-8"):
            diffs.extend(
                difflib.unified_diff(
                    repo_ref.read_text(encoding="utf-8").splitlines(True),
                    generated_ref.read_text(encoding="utf-8").splitlines(True),
                    fromfile=str(repo_ref),
                    tofile=str(generated_ref),
                )
            )

        if diffs:
            sys.stderr.write(
                "Generated artifacts are out of sync. Run "
                "`python3 scripts/generate_artifacts.py --write`.\n"
            )
            sys.stderr.writelines(diffs)
            return 1

    print("Generated artifacts are in sync.")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true", help="write generated artifacts")
    mode.add_argument("--check", action="store_true", help="check generated artifacts")
    args = parser.parse_args(argv)

    if args.write:
        generate(load_schema_bundle())
        print("Generated SDP artifacts.")
        return 0
    return check()


if __name__ == "__main__":
    raise SystemExit(main())
