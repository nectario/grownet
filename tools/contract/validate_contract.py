#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable


try:
    from jsonschema import Draft202012Validator
except Exception as import_error:  # pragma: no cover
    Draft202012Validator = None  # type: ignore[assignment]
    JSONSCHEMA_IMPORT_ERROR = import_error
else:  # pragma: no cover
    JSONSCHEMA_IMPORT_ERROR = None


@dataclass(frozen=True)
class ValidationIssue:
    path: str
    message: str


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate GrowNet contract JSON against its JSON Schema.")
    parser.add_argument(
        "--contract",
        default="docs/contracts/grownet.contract.v5.json",
        help="Path to authoritative contract JSON.",
    )
    parser.add_argument(
        "--schema",
        default="docs/contracts/grownet.contract.schema.json",
        help="Path to contract JSON Schema.",
    )
    parser.add_argument(
        "--require-evaluation-ku-bku",
        action="store_true",
        help="Fail if evaluation.knowledgeUnits.{ku,bku} is missing.",
    )
    return parser.parse_args(argv)


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as file_error:
        raise RuntimeError(f"Missing JSON file: {path}") from file_error
    except json.JSONDecodeError as decode_error:
        raise RuntimeError(f"Invalid JSON in {path}: {decode_error}") from decode_error


def json_path_to_pointer(parts: Iterable[Any]) -> str:
    escaped_parts: list[str] = []
    for part in parts:
        token = str(part).replace("~", "~0").replace("/", "~1")
        escaped_parts.append(token)
    return "/" + "/".join(escaped_parts) if escaped_parts else "/"


def validate_schema(contract: Any, schema: Any) -> list[ValidationIssue]:
    if Draft202012Validator is None:  # pragma: no cover
        raise RuntimeError(
            "Missing dependency: jsonschema. Install with:\n"
            "  python -m pip install jsonschema\n"
            f"Import error: {JSONSCHEMA_IMPORT_ERROR}"
        )

    validator = Draft202012Validator(schema)
    issues: list[ValidationIssue] = []
    for error in sorted(validator.iter_errors(contract), key=lambda err: list(err.path)):
        pointer = json_path_to_pointer(error.absolute_path)
        issues.append(ValidationIssue(path=pointer, message=error.message))
    return issues


def validate_evaluation_metadata(contract: Any) -> list[ValidationIssue]:
    evaluation = contract.get("evaluation")
    if not isinstance(evaluation, dict):
        return [ValidationIssue(path="/evaluation", message="Missing or invalid evaluation section (expected object).")]

    knowledge_units = evaluation.get("knowledgeUnits")
    if not isinstance(knowledge_units, dict):
        return [
            ValidationIssue(
                path="/evaluation/knowledgeUnits",
                message="Missing evaluation.knowledgeUnits (expected object).",
            )
        ]

    issues: list[ValidationIssue] = []
    for required_key in ("ku", "bku"):
        if required_key not in knowledge_units:
            issues.append(
                ValidationIssue(
                    path=f"/evaluation/knowledgeUnits/{required_key}",
                    message=f"Missing evaluation.knowledgeUnits.{required_key}.",
                )
            )
    return issues


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    contract_path = Path(args.contract)
    schema_path = Path(args.schema)

    contract = load_json(contract_path)
    schema = load_json(schema_path)

    issues = validate_schema(contract, schema)
    if args.require_evaluation_ku_bku:
        issues.extend(validate_evaluation_metadata(contract))

    if issues:
        print(f"[FAIL] Contract validation failed: {contract_path}")
        for issue in issues:
            print(f"- {issue.path}: {issue.message}")
        return 1

    print(f"[OK] Contract validated: {contract_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

