#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Write canonical GrowNet contract JSON with stable key ordering.")
    parser.add_argument(
        "--contract",
        default="docs/contracts/grownet.contract.v5.json",
        help="Path to authoritative contract JSON.",
    )
    parser.add_argument(
        "--out",
        default="docs/contracts/grownet.contract.v5.canonical.json",
        help="Path to write canonical JSON.",
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
    # Deterministic dict key order, stable indentation, stable unicode output.
    return json.dumps(obj, indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    contract_path = Path(args.contract)
    out_path = Path(args.out)

    contract_obj = load_json(contract_path)
    canonical_text = canonical_dumps(contract_obj)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(canonical_text, encoding="utf-8", newline="\n")

    print(f"[OK] Wrote canonical contract: {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

