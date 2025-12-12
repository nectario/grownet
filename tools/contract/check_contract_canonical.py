#!/usr/bin/env python3
from __future__ import annotations

import argparse
import difflib
import json
import sys
from pathlib import Path
from typing import Any


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Fail if canonical contract JSON is out of sync.")
    parser.add_argument(
        "--contract",
        default="docs/contracts/grownet.contract.v5.json",
        help="Path to authoritative contract JSON.",
    )
    parser.add_argument(
        "--canonical",
        default="docs/contracts/grownet.contract.v5.canonical.json",
        help="Path to canonical contract JSON.",
    )
    parser.add_argument(
        "--show-diff",
        action="store_true",
        help="Print a unified diff when out of sync.",
    )
    return parser.parse_args(argv)


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as file_error:
        raise RuntimeError(f"Missing JSON file: {path}") from file_error
    except json.JSONDecodeError as decode_error:
        raise RuntimeError(f"Invalid JSON in {path}: {decode_error}") from decode_error


def canonical_dumps(obj: Any) -> str:
    return json.dumps(obj, indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    contract_path = Path(args.contract)
    canonical_path = Path(args.canonical)

    contract_obj = load_json(contract_path)
    expected = canonical_dumps(contract_obj)

    if not canonical_path.exists():
        print(f"[FAIL] Missing canonical file: {canonical_path}")
        print("Run: python tools/contract/canonicalize_contract.py")
        return 1

    # Normalize CRLF in working trees (e.g. Windows autocrlf) so canonical checks
    # remain stable across platforms.
    actual = canonical_path.read_text(encoding="utf-8").replace("\r\n", "\n")
    if actual == expected:
        print(f"[OK] Canonical contract is in sync: {canonical_path}")
        return 0

    print("[FAIL] Canonical contract out of sync.")
    print(f"- authoritative: {contract_path}")
    print(f"- canonical:     {canonical_path}")
    print("Fix with: python tools/contract/canonicalize_contract.py")

    if args.show_diff:
        diff_lines = difflib.unified_diff(
            actual.splitlines(keepends=True),
            expected.splitlines(keepends=True),
            fromfile=str(canonical_path),
            tofile=str(contract_path) + " (canonicalized)",
        )
        sys.stdout.writelines(diff_lines)
    return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
