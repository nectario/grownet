#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class ParityResult:
    language: str
    contract_version: int
    tests: dict[str, Any]
    passed: bool
    skipped: bool
    skip_reason: str | None


PHASE1_TEST_KEYS = (
    "bus_decay_parity",
    "windowed_wiring_return_semantics",
    "one_growth_per_region_per_tick",
)


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run per-language parity scripts and aggregate results.")
    parser.add_argument(
        "--languages",
        default="python,java,cpp,mojo,typescript,rust",
        help="Comma-separated list of languages to attempt.",
    )
    parser.add_argument(
        "--required",
        default="python,java,cpp,typescript",
        help="Comma-separated list of languages required to pass (others may be skipped).",
    )
    return parser.parse_args(argv)


def load_contract_version(contract_path: Path) -> int:
    contract_obj = json.loads(contract_path.read_text(encoding="utf-8"))
    meta = contract_obj.get("meta", {})
    value = meta.get("contractVersion")
    if isinstance(value, str) and value.isdigit():
        return int(value)
    if isinstance(value, int):
        return value
    raise RuntimeError(f"Unexpected meta.contractVersion in {contract_path}: {value!r}")


def find_repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def run_script(script_path: Path, env: dict[str, str]) -> dict[str, Any]:
    completed = subprocess.run(
        [str(script_path)],
        cwd=str(find_repo_root()),
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    stdout_lines = [line for line in completed.stdout.splitlines() if line.strip()]
    json_line = None
    for line in reversed(stdout_lines):
        if line.lstrip().startswith("{") and line.rstrip().endswith("}"):
            json_line = line
            break
    if json_line is None:
        raise RuntimeError(
            f"{script_path.name} did not emit a JSON line.\n"
            f"exit={completed.returncode}\n"
            f"stdout:\n{completed.stdout}\n"
            f"stderr:\n{completed.stderr}\n"
        )
    try:
        result_obj = json.loads(json_line)
    except json.JSONDecodeError as decode_error:
        raise RuntimeError(
            f"{script_path.name} emitted invalid JSON: {decode_error}\n"
            f"line: {json_line}\n"
            f"stderr:\n{completed.stderr}\n"
        ) from decode_error
    result_obj["_exit"] = completed.returncode
    result_obj["_stderr"] = completed.stderr
    return result_obj


def normalize_result(result_obj: dict[str, Any]) -> ParityResult:
    language = str(result_obj.get("language", "unknown"))
    contract_version = int(result_obj.get("contractVersion", -1))
    tests = result_obj.get("tests", {})
    if not isinstance(tests, dict):
        tests = {}
    passed = bool(result_obj.get("pass", False))
    skipped = bool(result_obj.get("skipped", False))
    skip_reason = result_obj.get("skipReason")
    return ParityResult(
        language=language,
        contract_version=contract_version,
        tests=tests,
        passed=passed,
        skipped=skipped,
        skip_reason=str(skip_reason) if skip_reason is not None else None,
    )


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    repo_root = find_repo_root()
    contract_version = load_contract_version(repo_root / "docs/contracts/grownet.contract.v5.json")

    languages = [token.strip() for token in str(args.languages).split(",") if token.strip()]
    required = {token.strip() for token in str(args.required).split(",") if token.strip()}

    parity_dir = repo_root / "tools/contract/parity"
    results: list[ParityResult] = []
    raw_results: list[dict[str, Any]] = []
    failures: list[str] = []

    for language in languages:
        script_name = f"run_parity_{language}.sh"
        script_path = parity_dir / script_name
        if not script_path.exists():
            failures.append(f"Missing parity script: {script_path}")
            continue

        env = dict(os.environ)
        env["GROWNET_CONTRACT_VERSION"] = str(contract_version)
        try:
            result_obj = run_script(script_path, env)
        except Exception as error:
            failures.append(f"{language}: failed to run ({error})")
            continue
        raw_results.append(result_obj)
        results.append(normalize_result(result_obj))

    if failures:
        print("[FAIL] Parity harness failures:")
        for failure in failures:
            print(f"- {failure}")
        return 1

    for result in results:
        if result.contract_version != contract_version and not result.skipped:
            failures.append(
                f"{result.language}: contractVersion mismatch (got {result.contract_version}, expected {contract_version})"
            )

        # Ensure phase-1 keys exist (even if skipped) for consistent reporting.
        for key in PHASE1_TEST_KEYS:
            if key not in result.tests:
                failures.append(f"{result.language}: missing tests.{key} in parity output")

        if result.language in required and not result.passed:
            failures.append(f"{result.language}: required language did not pass (skipped={result.skipped})")

    out_path = repo_root / "tools/contract/parity/parity_results.json"
    out_path.write_text(json.dumps(raw_results, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    if failures:
        print("[FAIL] Parity results:")
        for failure in failures:
            print(f"- {failure}")
        print(f"Wrote: {out_path}")
        return 1

    print("[OK] Parity checks passed.")
    print(f"Wrote: {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

