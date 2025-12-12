#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable


@dataclass(frozen=True)
class PresenceFinding:
    required: str
    present: bool
    evidence: str | None


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Contract-driven signature presence scan (phase 1).")
    parser.add_argument(
        "--contract",
        default="docs/contracts/grownet.contract.v5.json",
        help="Path to authoritative contract JSON.",
    )
    parser.add_argument(
        "--out",
        default="tools/contract/parity/api_presence_report.json",
        help="Path to write report JSON.",
    )
    return parser.parse_args(argv)


def find_repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def extract_method_name(signature_line: str) -> str | None:
    match = re.search(r"([A-Za-z_][A-Za-z0-9_]*)\s*\(", signature_line)
    if match is None:
        return None
    return match.group(1)


def snake_to_camel(snake_name: str) -> str:
    parts = snake_name.split("_")
    if not parts:
        return snake_name
    head = parts[0]
    tail_parts: list[str] = []
    for part in parts[1:]:
        if part == "2d":
            tail_parts.append("2D")
        elif part == "nd":
            tail_parts.append("ND")
        else:
            tail_parts.append(part[:1].upper() + part[1:])
    return head + "".join(tail_parts)


def scan_files_for_tokens(paths: Iterable[Path], tokens: list[str], repo_root: Path) -> dict[str, PresenceFinding]:
    findings: dict[str, PresenceFinding] = {}
    for token in tokens:
        findings[token] = PresenceFinding(required=token, present=False, evidence=None)

    compiled = {token: re.compile(re.escape(token)) for token in tokens}
    for path in paths:
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue
        for token in tokens:
            if findings[token].present:
                continue
            if compiled[token].search(text) is not None:
                try:
                    evidence_path = path.relative_to(repo_root).as_posix()
                except ValueError:
                    evidence_path = path.as_posix()
                findings[token] = PresenceFinding(required=token, present=True, evidence=evidence_path)
    return findings


def list_source_files(language: str, repo_root: Path) -> list[Path]:
    if language == "python":
        return list((repo_root / "src/python").rglob("*.py"))
    if language == "cpp":
        return list((repo_root / "src/cpp").rglob("*.h")) + list((repo_root / "src/cpp").rglob("*.cpp"))
    if language == "java":
        return list((repo_root / "src/java").rglob("*.java"))
    if language == "mojo":
        return list((repo_root / "src/mojo").rglob("*.mojo"))
    if language == "typescript":
        return list((repo_root / "src/typescript/grownet-ts/src").rglob("*.ts"))
    if language == "rust":
        return list((repo_root / "src/rust").rglob("*.rs"))
    return []


def contract_phase1_required_tokens(contract_obj: dict[str, Any]) -> dict[str, dict[str, list[str]]]:
    # Phase 1 only: focus on the APIs needed by the phase-1 parity checks.
    required_by_language: dict[str, dict[str, list[str]]] = {}

    public_by_language = contract_obj.get("publicApisByLanguage", {})
    types = contract_obj.get("types", {})

    # Canonical method names from contract types (snake_case).
    region_methods = [m["name"] for m in types.get("Region", {}).get("methods", []) if isinstance(m, dict) and "name" in m]
    layer_methods = [m["name"] for m in types.get("Layer", {}).get("methods", []) if isinstance(m, dict) and "name" in m]

    # Minimal set for phase-1 enforcement scope.
    region_min = [
        "add_layer",
        "add_input_layer_2d",
        "add_output_layer_2d",
        "connect_layers_windowed",
        "set_growth_policy",
        "tick_2d",
    ]
    layer_min = [
        "end_tick",
        "try_grow_neuron",
    ]
    tract_min = [
        # Tract.attach_source_neuron is mandated by addendum; represented in publicApisByLanguage.
        "attach_source_neuron",
    ]
    slot_engine_min = [
        "select_or_create_slot",
        "select_or_create_slot_2d",
    ]

    # Python: snake_case scan for defs.
    required_by_language["python"] = {
        "Region": [f"def {name}" for name in region_min if name in region_methods],
        "Layer": [f"def {name}" for name in layer_min if name in layer_methods],
        "Tract": ["def attach_source_neuron"],
        "SlotEngine": [f"def {name}" for name in slot_engine_min],
    }

    # C++: use contract's public API signatures where available.
    cpp_api = public_by_language.get("cpp", {})
    cpp_slot_engine = []
    for signature in cpp_api.get("SlotEngine", {}).get("methods", []):
        name = extract_method_name(signature)
        if name:
            cpp_slot_engine.append(name)
    required_by_language["cpp"] = {
        "Region": ["connectLayersWindowed", "requestLayerGrowth", "maybeGrowRegion"],
        "Layer": ["endTick", "tryGrowNeuron"],
        "Tract": ["attachSourceNeuron"],
        "SlotEngine": cpp_slot_engine or ["selectOrCreateSlot", "selectOrCreateSlot2D"],
    }

    # Java: use contract public API section (camelCase).
    java_api = public_by_language.get("java", {})
    java_slot_engine = []
    for signature in java_api.get("SlotEngine", {}).get("methods", []):
        name = extract_method_name(signature)
        if name:
            java_slot_engine.append(name)
    required_by_language["java"] = {
        "Region": ["connectLayersWindowed", "requestLayerGrowth", "maybeGrowRegion"],
        "Layer": ["endTick", "tryGrowNeuron"],
        "Tract": ["attachSourceNeuron"],
        "SlotEngine": java_slot_engine or ["selectOrCreateSlot", "selectOrCreateSlot2D"],
    }

    # Mojo: snake_case function names.
    required_by_language["mojo"] = {
        "Region": ["fn connect_layers_windowed", "fn request_layer_growth"],
        "Layer": ["fn end_tick", "fn try_grow_neuron"],
        "Tract": ["fn attach_source_neuron"],
        "SlotEngine": ["fn select_or_create_slot", "fn select_or_create_slot_2d"],
    }

    # TypeScript: camelCase methods.
    required_by_language["typescript"] = {
        "Region": ["connectLayersWindowed", "setGrowthPolicy", "tick2D", "tickND"],
        "Layer": ["endTick", "tryGrowNeuron"],
        "Tract": ["attachSourceNeuron"],
        "SlotEngine": [],  # TS does not expose SlotEngine as a public type in v5 contract.
    }

    # Rust: snake_case methods (only minimal set; Rust implementation is staged).
    required_by_language["rust"] = {
        "Region": ["connect_layers_windowed", "tick_2d"],
        "Layer": ["end_tick"],
        "Tract": ["attach_source_neuron"],
        "SlotEngine": ["observe_scalar", "observe_two_d"],
    }

    return required_by_language


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    repo_root = find_repo_root()

    contract_obj = load_json(repo_root / args.contract)
    required_by_language = contract_phase1_required_tokens(contract_obj)

    report: dict[str, Any] = {
        "contractVersion": int(str(contract_obj.get("meta", {}).get("contractVersion", "0"))),
        "languages": {},
    }

    overall_failures: list[str] = []
    for language, categories in required_by_language.items():
        source_files = list_source_files(language, repo_root)
        all_tokens: list[str] = []
        for tokens in categories.values():
            all_tokens.extend(tokens)

        findings = scan_files_for_tokens(source_files, all_tokens, repo_root)
        report_language: dict[str, Any] = {"categories": {}, "pass": True}

        for category_name, tokens in categories.items():
            category_findings: list[dict[str, Any]] = []
            for token in tokens:
                finding = findings[token]
                category_findings.append(
                    {"required": finding.required, "present": finding.present, "evidence": finding.evidence}
                )
            missing = [f for f in category_findings if not f["present"]]
            report_language["categories"][category_name] = {
                "requiredCount": len(tokens),
                "missingCount": len(missing),
                "findings": category_findings,
            }
            if missing:
                report_language["pass"] = False

        report["languages"][language] = report_language
        if not report_language["pass"]:
            overall_failures.append(language)

    out_path = repo_root / args.out
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    if overall_failures:
        print("[FAIL] API presence check failed for:", ", ".join(sorted(overall_failures)))
        print(f"Wrote: {out_path}")
        return 1

    print("[OK] API presence check passed.")
    print(f"Wrote: {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
