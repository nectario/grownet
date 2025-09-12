#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
API Diff: Python ↔ Mojo (GrowNet)

Compares the discovered public API surfaces of the Python and Mojo trees,
optionally projects expected API from the v5 contract YAML, and emits a
Markdown report with a divergence score and concrete diffs.

Assumptions (from GrowNet v5 contract/spec & style guides):
- Python + Mojo public API uses snake_case; no leading underscores in public names.
- Keep cross-language public APIs aligned; contract is the source of truth for signatures.
- We only compare public surfaces; private helpers (leading '_') are ignored.
"""

import argparse
import ast
import json
import os
import re
import sys
from collections import defaultdict, namedtuple
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple, Iterable

try:
    import yaml  # PyYAML
except Exception:
    yaml = None  # Contract projection becomes best-effort if PyYAML is absent


# ---------- Models ----------

@dataclass(frozen=True)
class SymbolSig:
    container: Optional[str]      # class/struct name or None for module-level
    name: str                     # function/method name
    arity: int                    # positional params (best-effort)
    kind: str                     # 'function' | 'method' | 'ctor'

    def key_no_arity(self) -> Tuple[Optional[str], str, str]:
        return (self.container, self.name, self.kind)

@dataclass
class ApiSurface:
    functions: Set[SymbolSig] = field(default_factory=set)
    methods:   Set[SymbolSig] = field(default_factory=set)
    ctors:     Set[SymbolSig] = field(default_factory=set)

    def all_symbols(self) -> Set[SymbolSig]:
        return set().union(self.functions, self.methods, self.ctors)


# ---------- Helpers ----------

PY_PUBLIC_NAME = re.compile(r'^[a-z][a-z0-9_]*$')        # snake_case, no leading underscore
MOJO_STRUCT_DEF = re.compile(r'^\s*struct\s+([A-Za-z_][A-Za-z0-9_]*)\s*:', re.MULTILINE)
MOJO_FN_DEF     = re.compile(r'^\s*fn\s+([a-z_][a-z0-9_]*)\s*\((.*?)\)\s*(->\s*[\w\[\]<>:, ]+)?\s*:', re.MULTILINE | re.DOTALL)

def walk_files(root: str, extensions: Tuple[str, ...]) -> Iterable[str]:
    for dirpath, _, filenames in os.walk(root):
        for fname in filenames:
            if fname.endswith(extensions):
                yield os.path.join(dirpath, fname)

def count_positional(arg_nodes: List[ast.arg]) -> int:
    return len(arg_nodes)

def safe_read_text(path: str) -> str:
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        return f.read()

# ---------- Python parsing ----------

def parse_python_api(root: str) -> ApiSurface:
    surface = ApiSurface()
    for path in walk_files(root, (".py",)):
        try:
            module = ast.parse(safe_read_text(path), filename=path)
        except SyntaxError:
            continue
        for node in module.body:
            # Top-level functions
            if isinstance(node, ast.FunctionDef):
                if not node.name.startswith("_") and PY_PUBLIC_NAME.match(node.name):
                    arity = count_positional([a for a in node.args.args])
                    surface.functions.add(SymbolSig(None, node.name, arity, "function"))
            # Classes
            if isinstance(node, ast.ClassDef):
                class_name = node.name
                for citem in node.body:
                    if isinstance(citem, ast.FunctionDef):
                        name_ok = not citem.name.startswith("_") and PY_PUBLIC_NAME.match(citem.name)
                        if not name_ok:
                            continue
                        # Determine method kind (ctor vs method)
                        if citem.name in ("__init__",):
                            arity = max(0, count_positional([a for a in citem.args.args]) - 1)  # drop self
                            surface.ctors.add(SymbolSig(class_name, "__init__", arity, "ctor"))
                        else:
                            arity = max(0, count_positional([a for a in citem.args.args]) - 1)  # drop self
                            surface.methods.add(SymbolSig(class_name, citem.name, arity, "method"))
    return surface

# ---------- Mojo parsing (regex, best effort) ----------

def parse_mojo_api(root: str) -> ApiSurface:
    surface = ApiSurface()
    for path in walk_files(root, (".mojo",)):
        text = safe_read_text(path)

        # Discover structs
        struct_spans = [(m.group(1), m.start()) for m in MOJO_STRUCT_DEF.finditer(text)]
        struct_spans.append(("_MODULE_", len(text)))  # sentinel

        # For each struct block, find fn declarations until next struct
        for idx in range(len(struct_spans) - 1):
            struct_name, start_pos = struct_spans[idx]
            _, end_pos = struct_spans[idx + 1]
            block = text[start_pos:end_pos]

            for fm in MOJO_FN_DEF.finditer(block):
                fn_name = fm.group(1)
                params_blob = fm.group(2) or ""
                params_blob = params_blob.strip()

                # Public only: snake_case, no leading underscores
                if fn_name.startswith("_") or not re.match(r'^[a-z][a-z0-9_]*$', fn_name):
                    continue

                # Count parameters (rough): split by commas not inside <> or []
                if not params_blob:
                    arity = 0
                else:
                    # remove self-like params commonly used in Mojo methods
                    raw_params = [p.strip() for p in params_blob.split(",") if p.strip()]
                    filtered_params = [p for p in raw_params if not re.match(r'^(self\s*:|self\b)', p)]
                    arity = len(filtered_params)

                if struct_name == "_MODULE_":
                    surface.functions.add(SymbolSig(None, fn_name, arity, "function"))
                else:
                    surface.methods.add(SymbolSig(struct_name, fn_name, arity, "method"))
    return surface

# ---------- Contract projection (best-effort) ----------

def load_contract_api(contract_path: Optional[str], languages: Tuple[str, ...]) -> Dict[str, Set[str]]:
    if not contract_path or not os.path.exists(contract_path) or yaml is None:
        return {lang: set() for lang in languages}
    try:
        with open(contract_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
    except Exception:
        return {lang: set() for lang in languages}

    def gather_strings(node) -> Set[str]:
        names = set()
        if isinstance(node, str):
            if re.match(r'^[A-Za-z_][A-Za-z0-9_]*$', node):
                names.add(node)
        elif isinstance(node, list):
            for item in node:
                names |= gather_strings(item)
        elif isinstance(node, dict):
            for key, val in node.items():
                names |= gather_strings(key)
                names |= gather_strings(val)
        return names

    # Heuristic: search subtrees named exactly by language or containing language as key
    projected = {}
    for lang in languages:
        lang_nodes: List = []

        def dfs(node):
            if isinstance(node, dict):
                for k, v in node.items():
                    if str(k).strip().lower() == lang.lower():
                        lang_nodes.append(v)
                    dfs(v)
            elif isinstance(node, list):
                for it in node:
                    dfs(it)

        dfs(data)
        # Fall back to scanning entire document for symbol-like strings
        names = set()
        for ln in lang_nodes:
            names |= gather_strings(ln)
        if not names:
            names = gather_strings(data)
        projected[lang] = names
    return projected

# ---------- Diff & report ----------

@dataclass
class DiffReport:
    missing_in_mojo: List[SymbolSig] = field(default_factory=list)
    missing_in_python: List[SymbolSig] = field(default_factory=list)
    arity_mismatches: List[Tuple[SymbolSig, SymbolSig]] = field(default_factory=list)
    extras_vs_contract: Dict[str, List[SymbolSig]] = field(default_factory=lambda: defaultdict(list))
    missing_vs_contract: Dict[str, List[str]] = field(default_factory=lambda: defaultdict(list))
    style_flags: Dict[str, List[str]] = field(default_factory=lambda: defaultdict(list))
    divergence_score: float = 0.0
    totals: Dict[str, int] = field(default_factory=dict)

def compute_diff(py: ApiSurface, mj: ApiSurface, contract_syms: Dict[str, Set[str]]) -> DiffReport:
    report = DiffReport()
    py_syms = py.all_symbols()
    mj_syms = mj.all_symbols()

    # Compare presence ignoring arity first
    py_keys = {s.key_no_arity(): s for s in py_syms}
    mj_keys = {s.key_no_arity(): s for s in mj_syms}

    for key, psig in py_keys.items():
        if key not in mj_keys:
            report.missing_in_mojo.append(psig)

    for key, msig in mj_keys.items():
        if key not in py_keys:
            report.missing_in_python.append(msig)

    # Compare arity for common names
    common_keys = set(py_keys.keys()) & set(mj_keys.keys())
    for key in sorted(common_keys):
        psig, msig = py_keys[key], mj_keys[key]
        if psig.arity != msig.arity:
            report.arity_mismatches.append((psig, msig))

    # Contract projection (best-effort)
    if contract_syms.get("python"):
        py_names = {s.name for s in py_syms}
        missing = sorted(n for n in contract_syms["python"] if n not in py_names)
        if missing:
            report.missing_vs_contract["python"] = missing
        extras = sorted(n for n in py_names if contract_syms["python"] and n not in contract_syms["python"])
        if extras:
            report.extras_vs_contract["python"] = [s for s in py_syms if s.name in extras]

    if contract_syms.get("mojo"):
        mj_names = {s.name for s in mj_syms}
        missing = sorted(n for n in contract_syms["mojo"] if n not in mj_names)
        if missing:
            report.missing_vs_contract["mojo"] = missing
        extras = sorted(n for n in mj_names if contract_syms["mojo"] and n not in contract_syms["mojo"])
        if extras:
            report.extras_vs_contract["mojo"] = [s for s in mj_syms if s.name in extras]

    # Divergence score (0 = perfect, 100 = totally disjoint)
    union_count = len(set(py_keys.keys()) | set(mj_keys.keys()))
    diff_count = len(report.missing_in_mojo) + len(report.missing_in_python) + len(report.arity_mismatches)
    report.divergence_score = (100.0 * diff_count / union_count) if union_count else 0.0

    # Totals
    report.totals = {
        "python_public": len(py_syms),
        "mojo_public": len(mj_syms),
        "union": union_count,
        "missing_in_mojo": len(report.missing_in_mojo),
        "missing_in_python": len(report.missing_in_python),
        "arity_mismatches": len(report.arity_mismatches),
    }
    return report

def render_markdown(report: DiffReport) -> str:
    out: List[str] = []
    out.append("# GrowNet API Diff — Python ↔ Mojo\n")
    out.append(f"**Divergence score:** {report.divergence_score:.2f}%  \n")
    out.append("Totals: " + ", ".join(f"{k}={v}" for k, v in report.totals.items()) + "\n")

    def fmt_sig(s: SymbolSig) -> str:
        head = f"{s.container + '.' if s.container else ''}{s.name}"
        return f"- `{head}` ({s.kind}, arity={s.arity})"

    if report.missing_in_mojo:
        out.append("\n## Missing in Mojo (present in Python)\n")
        out.extend(fmt_sig(s) for s in sorted(report.missing_in_mojo, key=lambda x: (x.container or "", x.name)))
    if report.missing_in_python:
        out.append("\n## Missing in Python (present in Mojo)\n")
        out.extend(fmt_sig(s) for s in sorted(report.missing_in_python, key=lambda x: (x.container or "", x.name)))
    if report.arity_mismatches:
        out.append("\n## Arity mismatches (same name, different param counts)\n")
        for psig, msig in sorted(report.arity_mismatches, key=lambda p: (p[0].container or "", p[0].name)):
            out.append(f"- `{(psig.container + '.' if psig.container else '')}{psig.name}`: Python={psig.arity}, Mojo={msig.arity}")

    if report.missing_vs_contract:
        out.append("\n## Missing vs Contract (best-effort projection)\n")
        for lang, names in report.missing_vs_contract.items():
            out.append(f"- **{lang}** missing: " + ", ".join(f"`{n}`" for n in names))
    if report.extras_vs_contract:
        out.append("\n## Extras vs Contract (best-effort projection)\n")
        for lang, syms in report.extras_vs_contract.items():
            out.append(f"- **{lang}** extras:")
            for s in syms:
                out.append(f"  {fmt_sig(s)}")

    out.append("\n---\n_This report compares public snake_case symbols (no leading underscores). Contract projection is heuristic if the YAML does not expose per-language sections explicitly._\n")
    return "\n".join(out)

# ---------- CLI ----------

def main() -> int:
    parser = argparse.ArgumentParser(description="API diff: Python ↔ Mojo (GrowNet)")
    parser.add_argument("--python-root", required=True, help="Path to Python source root (e.g., ./src/python)")
    parser.add_argument("--mojo-root",   required=True, help="Path to Mojo source root (e.g., ./src/mojo)")
    parser.add_argument("--contract-yaml", required=False, default=None, help="Path to v5 contract yaml (optional)")
    args = parser.parse_args()

    py_surface = parse_python_api(args.python_root)
    mj_surface = parse_mojo_api(args.mojo_root)

    contract_syms = load_contract_api(args.contract_yaml, ("python", "mojo"))
    report = compute_diff(py_surface, mj_surface, contract_syms)
    sys.stdout.write(render_markdown(report) + "\n")
    return 0

if __name__ == "__main__":
    sys.exit(main())
