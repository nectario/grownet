#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
api_diff_grownet.py

Compare public API of the Java and C++ codebases against the GrowNet v5 contract
AND against each other (Java ⇄ C++). Emits a Markdown report to stdout.

Usage
-----
python3 api_diff_grownet.py \
  --cpp-root ./src/cpp \
  --java-root ./src/java \
  --contract-yaml ./GrowNet_Contract_v5_master.yaml \
  [--fail-on-diff] \
  [--skip-dirs tests demo build cmake-build-debug .git] \
  [--cpp-include-exts h hpp hh hxx cpp cc cxx] \
  [--java-include-exts java]

Notes
-----
- Requires PyYAML (pip install pyyaml). If not present, the script still runs
  (contract parsing falls back to "not available" and only Java⇄C++ parity is reported).
- We compare by (method_name, param_count) primarily, to avoid false positives due
  to language-specific type spellings. We also print types when available.
- C++ extraction:
  * Parses headers for class public sections, and .cpp for out-of-class definitions.
  * Only files in --cpp-root are scanned; demo/tests/hidden dirs are skipped by default.
- Java extraction:
  * Scans public classes and public methods (excludes constructors and fields).
- Contract extraction:
  * Tries several YAML shapes. See _extract_contract_api() for details.

Exit code
---------
0 if no diffs OR contract not provided; 1 if --fail-on-diff is set and any diffs were found.

Author
------
GrowNet API parity tooling.
"""

import argparse
import os
import re
import sys
from collections import defaultdict
from dataclasses import dataclass
from typing import Dict, List, Set, Tuple, Optional

# Optional YAML
try:
    import yaml  # PyYAML
    _HAVE_YAML = True
except Exception:
    _HAVE_YAML = False


# ---------- Utility types ----------

@dataclass(frozen=True)
class MethodSigKey:
    """Key used for parity comparison (strict name + arity)."""
    name: str           # case-sensitive
    arity: int

    def casefold_key(self) -> Tuple[str, int]:
        return (self.name.casefold(), self.arity)


@dataclass
class MethodSigRecord:
    """Holds the original signature text/parts to show in the report."""
    name: str
    arity: int
    return_type: Optional[str] = None
    param_types: Optional[List[str]] = None
    raw: Optional[str] = None  # unparsed line for context


@dataclass
class ClassAPI:
    """All public methods keyed by (name, arity)."""
    class_name: str
    methods: Dict[MethodSigKey, List[MethodSigRecord]]


@dataclass
class LanguageAPI:
    """Mapping class -> ClassAPI for a codebase (C++ or Java)."""
    language: str
    classes: Dict[str, ClassAPI]


# ---------- Helpers ----------

DEFAULT_SKIP_DIRS = {"tests", "test", "demo", "demos", "build", "out", "cmake-build-debug", ".git", ".idea", ".vscode", "_deps"}
DEFAULT_CPP_EXTS = {"h", "hpp", "hh", "hxx", "cpp", "cc", "cxx"}
DEFAULT_JAVA_EXTS = {"java"}

RE_CXX_CLASS_START = re.compile(r'^\s*(class|struct)\s+([A-Za-z_]\w*)\s*(?:[:{]|$)')
RE_CXX_ACCESS = re.compile(r'^\s*(public|private|protected)\s*:')  # note: only matches 'public:' etc.
RE_CXX_METHOD_SEMI = re.compile(r';\s*$')  # end of method decl (header)
RE_CXX_OUT_OF_CLASS_DEF = re.compile(
    r'^[\s\w:<>\*&\[\],~]+?\b([A-Za-z_]\w*)::([A-Za-z_]\w*)\s*\(([^)]*)\)\s*(?:const\b|noexcept\b|throw\s*\([^)]*\))?\s*[{;]'
)

RE_JAVA_PUBLIC_CLASS = re.compile(r'\bpublic\s+(?:final\s+|abstract\s+)?(?:class|interface|enum)\s+([A-Za-z_]\w*)\b')
RE_JAVA_PUBLIC_METHOD = re.compile(
    r'\bpublic\s+(?:static\s+|default\s+|final\s+|abstract\s+|synchronized\s+|native\s+)*'
    r'(?:[A-Za-z_][\w<>\[\]\.? ,]+)\s+([A-Za-z_]\w*)\s*\(([^)]*)\)\s*(?:throws\b[^;{]*)?(?:[{;])'
)
RE_JAVA_CONSTRUCTOR = re.compile(r'\bpublic\s+([A-Za-z_]\w*)\s*\(')

RE_CAMEL_TOKEN = re.compile(r'[A-Z]?[a-z]+|[A-Z]+(?![a-z])|\d+D|\d+')

def iter_files(root: str, include_exts: Set[str], skip_dirs: Set[str]) -> List[str]:
    files = []
    for base, dirs, fs in os.walk(root):
        # trim skip dirs in-place
        dirs[:] = [d for d in dirs if d not in skip_dirs and not d.startswith('.')]
        for f in fs:
            ext = f.rsplit('.', 1)[-1].lower() if '.' in f else ''
            if ext in include_exts:
                files.append(os.path.join(base, f))
    return files


def _split_params_list(params: str) -> List[str]:
    # Very loose split by commas that are not inside angle brackets
    out, depth, cur = [], 0, []
    for ch in params:
        if ch == '<':
            depth += 1
        elif ch == '>':
            depth = max(0, depth - 1)
        if ch == ',' and depth == 0:
            part = ''.join(cur).strip()
            if part:
                out.append(part)
            cur = []
        else:
            cur.append(ch)
    last = ''.join(cur).strip()
    if last:
        out.append(last)
    return out


def _clean_type(t: str) -> str:
    # Normalize types a bit (remove const, refs, namespaces)
    t = t.strip()
    t = re.sub(r'\bconst\b', '', t)
    t = t.replace('&', '').replace('*', '')
    t = re.sub(r'\b(std::|java\.util\.|java\.lang\.)', '', t)
    t = re.sub(r'\s+', ' ', t).strip()
    return t


def _parse_params(param_blob: str) -> List[str]:
    if not param_blob.strip():
        return []
    raw_parts = _split_params_list(param_blob)
    parts = []
    for p in raw_parts:
        # remove default values / annotations
        p = re.sub(r'@[\w.]+\s*', '', p)  # Java annotations
        p = re.sub(r'=\s*[^,]+$', '', p)  # default values (C++)
        # split "type name" (keep only type)
        tokens = p.strip().split()
        if len(tokens) == 1:
            parts.append(_clean_type(tokens[0]))
        else:
            # Best-effort: assume last token is variable name (strip [] for arrays)
            type_part = ' '.join(tokens[:-1])
            parts.append(_clean_type(type_part))
    return parts


def _tokens_from_camel(name: str) -> List[str]:
    return [t for t in RE_CAMEL_TOKEN.findall(name) if t]


# ---------- C++ extraction ----------

def extract_cpp_api(cpp_root: str,
                    include_exts: Set[str],
                    skip_dirs: Set[str]) -> LanguageAPI:
    classes: Dict[str, ClassAPI] = {}
    files = iter_files(cpp_root, include_exts, skip_dirs)

    # Pass 1: scan headers for class public methods
    for path in files:
        if not re.search(r'\.(h|hpp|hh|hxx)$', path, re.I):
            continue
        with open(path, 'r', encoding='utf-8', errors='ignore') as fh:
            text = fh.read()

        # crude namespace stripping is unnecessary; we just find class blocks
        pos = 0
        while True:
            m = RE_CXX_CLASS_START.search(text, pos)
            if not m:
                break
            class_name = m.group(2)
            # find matching brace (naive; tolerates most headers)
            brace_start = text.find('{', m.end())
            if brace_start == -1:
                pos = m.end()
                continue
            depth, i = 1, brace_start + 1
            while i < len(text) and depth > 0:
                if text[i] == '{':
                    depth += 1
                elif text[i] == '}':
                    depth -= 1
                i += 1
            class_block = text[brace_start+1:i-1] if depth == 0 else text[brace_start+1:]

            # slice public sections
            public_chunks: List[str] = []
            acc_mode = None
            for line in class_block.splitlines():
                acc_m = RE_CXX_ACCESS.match(line)
                if acc_m:
                    acc_mode = acc_m.group(1)
                    continue
                if acc_mode == 'public':
                    public_chunks.append(line)
            public_text = '\n'.join(public_chunks)

            # collect method prototypes ending with ';' that look like funcs
            # allow multi-line prototypes
            buf, methods = [], []
            for line in public_text.splitlines():
                # skip obvious fields or comments
                if re.match(r'^\s*(//|/\*|\*|\*/)', line):
                    continue
                buf.append(line)
                if RE_CXX_METHOD_SEMI.search(line):
                    stmt = ' '.join(s.strip() for s in buf).strip()
                    buf = []
                    if '(' in stmt and ')' in stmt:
                        # exclude constructors/destructors
                        name_m = re.search(r'([A-Za-z_]\w*)\s*\(', stmt)
                        if not name_m:
                            continue
                        name = name_m.group(1)
                        if name == class_name or name == f'~{class_name}':
                            continue
                        # parse params
                        params_blob_m = re.search(r'\(([^)]*)\)', stmt)
                        params_blob = params_blob_m.group(1) if params_blob_m else ''
                        params = _parse_params(params_blob)
                        arity = len(params)
                        ret_m = re.search(r'^\s*([A-Za-z_:<>\s\*\&]+?)\s+[A-Za-z_]\w*\s*\(', stmt)
                        ret_type = None
                        if ret_m:
                            ret_type = _clean_type(ret_m.group(1))
                        key = MethodSigKey(name=name, arity=arity)
                        rec = MethodSigRecord(name=name, arity=arity, return_type=ret_type,
                                              param_types=params, raw=stmt)
                        classes.setdefault(class_name, ClassAPI(class_name, {})).methods.setdefault(key, []).append(rec)

            pos = i if depth == 0 else m.end()

    # Pass 2: pick up out-of-class definitions in .cpp
    for path in files:
        if not re.search(r'\.(cpp|cc|cxx)$', path, re.I):
            continue
        with open(path, 'r', encoding='utf-8', errors='ignore') as fh:
            for ln in fh:
                m = RE_CXX_OUT_OF_CLASS_DEF.match(ln.strip())
                if not m:
                    continue
                class_name, method_name, params_blob = m.group(1), m.group(2), m.group(3)
                # exclude dtors/ctors
                if method_name == class_name or method_name == f'~{class_name}':
                    continue
                params = _parse_params(params_blob)
                key = MethodSigKey(method_name, len(params))
                rec = MethodSigRecord(name=method_name, arity=len(params), param_types=params, raw=ln.strip())
                classes.setdefault(class_name, ClassAPI(class_name, {})).methods.setdefault(key, []).append(rec)

    return LanguageAPI(language="C++", classes=classes)


# ---------- Java extraction ----------

def extract_java_api(java_root: str,
                     include_exts: Set[str],
                     skip_dirs: Set[str]) -> LanguageAPI:
    classes: Dict[str, ClassAPI] = {}
    files = iter_files(java_root, include_exts, skip_dirs)

    for path in files:
        with open(path, 'r', encoding='utf-8', errors='ignore') as fh:
            text = fh.read()

        # find each public class/interface/enum in the file
        for class_m in RE_JAVA_PUBLIC_CLASS.finditer(text):
            class_name = class_m.group(1)

            # naive: consider from class start to next class or EOF
            start = class_m.start()
            # find next 'public class|interface|enum' start
            next_m = RE_JAVA_PUBLIC_CLASS.search(text, class_m.end())
            end = next_m.start() if next_m else len(text)
            block = text[start:end]

            # extract public methods (exclude constructors)
            for meth_m in RE_JAVA_PUBLIC_METHOD.finditer(block):
                method_name = meth_m.group(1)
                # skip constructors (public ClassName(...))
                if RE_JAVA_CONSTRUCTOR.search(meth_m.group(0)):
                    continue
                params_blob = meth_m.group(2)
                params = _parse_params(params_blob)
                key = MethodSigKey(method_name, len(params))
                rec = MethodSigRecord(name=method_name, arity=len(params), param_types=params, raw=meth_m.group(0))
                classes.setdefault(class_name, ClassAPI(class_name, {})).methods.setdefault(key, []).append(rec)

    return LanguageAPI(language="Java", classes=classes)


# ---------- Contract extraction ----------

def _extract_contract_api(contract_yaml_path: str) -> Optional[LanguageAPI]:
    if not _HAVE_YAML:
        return None
    try:
        with open(contract_yaml_path, 'r', encoding='utf-8') as fh:
            data = yaml.safe_load(fh)
    except Exception as e:
        print(f"[warn] Failed to load YAML: {e}", file=sys.stderr)
        return None

    # We try a few shapes:
    # 1) top-level: {'classes': [{'name': 'Region', 'methods': [{'name': 'tick', 'params': [...]}, {'signature': 'int addLayer(int,int,int)'}]}]}
    # 2) nested: {'api': {'classes': [...]}}
    # 3) per-language: {'java': {'classes': [...]}, 'cpp': {'classes': [...]}} → union of both
    # 4) map of class names: {'Region': {'methods': [...]}, 'Layer': {...}}
    # 5) anywhere else: search all dict nodes with key 'classes' and collect unions.

    def collect_from_classes_list(classes_list, acc: Dict[str, ClassAPI]):
        for c in classes_list or []:
            cname = c.get('name') or c.get('class') or c.get('type') or c.get('id')
            if not cname:
                continue
            class_api = acc.setdefault(cname, ClassAPI(cname, {}))
            methods = c.get('methods') or c.get('operations') or c.get('functions') or []
            for m in methods:
                if isinstance(m, str):
                    # parse like: "int addLayer(int excit, int inhib, int mod)"
                    sig = m
                    name_m = re.search(r'\b([A-Za-z_]\w*)\s*\(', sig)
                    if not name_m:
                        continue
                    name = name_m.group(1)
                    params_blob_m = re.search(r'\(([^)]*)\)', sig)
                    params_blob = params_blob_m.group(1) if params_blob_m else ''
                    params = _parse_params(params_blob)
                    key = MethodSigKey(name, len(params))
                    rec = MethodSigRecord(name, len(params), raw=sig)
                    class_api.methods.setdefault(key, []).append(rec)
                elif isinstance(m, dict):
                    name = m.get('name') or m.get('id')
                    if not name and 'signature' in m:
                        sig = m['signature']
                        name_m = re.search(r'\b([A-Za-z_]\w*)\s*\(', sig)
                        if not name_m:
                            continue
                        name = name_m.group(1)
                        params_blob_m = re.search(r'\(([^)]*)\)', sig)
                        params_blob = params_blob_m.group(1) if params_blob_m else ''
                        params = _parse_params(params_blob)
                        key = MethodSigKey(name, len(params))
                        rec = MethodSigRecord(name, len(params), raw=sig)
                        class_api.methods.setdefault(key, []).append(rec)
                    else:
                        params_spec = m.get('params') or m.get('parameters') or []
                        params = []
                        for p in params_spec:
                            if isinstance(p, str):
                                params.append(_clean_type(p))
                            elif isinstance(p, dict):
                                t = p.get('type') or p.get('kind') or ''
                                params.append(_clean_type(t))
                        key = MethodSigKey(name, len(params))
                        rec = MethodSigRecord(name, len(params), param_types=params)
                        class_api.methods.setdefault(key, []).append(rec)

    def walk_collect(node, acc: Dict[str, ClassAPI]):
        if isinstance(node, dict):
            # case 1/2
            if 'classes' in node and isinstance(node['classes'], list):
                collect_from_classes_list(node['classes'], acc)
            # case 4
            else:
                # class-map style
                # detect child with 'methods'
                if 'methods' in node and isinstance(node['methods'], list) and 'name' in node:
                    collect_from_classes_list([node], acc)
                # continue walking
                for v in node.values():
                    walk_collect(v, acc)
        elif isinstance(node, list):
            for v in node:
                walk_collect(v, acc)

    # Start with per-language union if present
    acc: Dict[str, ClassAPI] = {}
    if isinstance(data, dict):
        for k in ('java', 'Java', 'cpp', 'C++', 'cxx', 'api', 'API'):
            if k in data and isinstance(data[k], dict):
                walk_collect(data[k], acc)
    # Fallback to whole tree
    if not acc:
        walk_collect(data, acc)

    if not acc:
        return None
    return LanguageAPI(language="Contract(v5)", classes=acc)


# ---------- Diff and report ----------

def diff_lang_vs_contract(lang: LanguageAPI, contract: LanguageAPI) -> Dict[str, Dict[str, List[str]]]:
    """Return per-class: missing_in_lang, extra_in_lang (relative to contract)."""
    report: Dict[str, Dict[str, List[str]]] = {}
    for cname, cclass in contract.classes.items():
        lang_class = lang.classes.get(cname)
        want = set(cclass.methods.keys())
        have = set(lang_class.methods.keys()) if lang_class else set()
        missing = sorted([f"{k.name}/{k.arity}" for k in (want - have)])
        extra = sorted([f"{k.name}/{k.arity}" for k in (have - want)])
        report[cname] = {
            "missing_in_" + lang.language.replace("+", "p"): missing,
            "extra_in_" + lang.language.replace("+", "p"): extra
        }
    # Also detect classes present in lang but not in contract
    for cname in lang.classes.keys():
        if cname not in contract.classes:
            report.setdefault(cname, {})
            report[cname]["extra_in_" + lang.language.replace("+", "p")] = sorted(
                [f"{k.name}/{k.arity}" for k in lang.classes[cname].methods.keys()]
            )
    return report


def diff_java_cpp(java_api: LanguageAPI, cpp_api: LanguageAPI) -> Dict[str, Dict[str, List[str]]]:
    """Return per-class diffs between Java and C++ (strict name + arity)."""
    report: Dict[str, Dict[str, List[str]]] = {}
    all_classes = set(java_api.classes.keys()) | set(cpp_api.classes.keys())
    for cname in sorted(all_classes):
        j = java_api.classes.get(cname)
        c = cpp_api.classes.get(cname)
        jset = set(j.methods.keys()) if j else set()
        cset = set(c.methods.keys()) if c else set()
        missing_in_java = sorted([f"{k.name}/{k.arity}" for k in (cset - jset)])
        missing_in_cpp = sorted([f"{k.name}/{k.arity}" for k in (jset - cset)])

        # case-insensitive hints (same arity, different case)
        j_fold = defaultdict(list)
        for k in jset:
            j_fold[k.casefold_key()].append(k)
        c_fold = defaultdict(list)
        for k in cset:
            c_fold[k.casefold_key()].append(k)

        case_only_mismatches = []
        for cf_key, j_keys in j_fold.items():
            if cf_key in c_fold:
                # names differ only by case (or Java vs C++ convention)
                for jk in j_keys:
                    for ck in c_fold[cf_key]:
                        if jk.name != ck.name and jk.arity == ck.arity:
                            case_only_mismatches.append(f"Java:{jk.name}/{jk.arity}  ↔  C++:{ck.name}/{ck.arity}")

        report[cname] = {
            "missing_in_java": missing_in_java,
            "missing_in_cpp": missing_in_cpp,
            "case_only_mismatches": sorted(set(case_only_mismatches)),
        }
    return report


def print_markdown_report(args,
                          contract_api: Optional[LanguageAPI],
                          cpp_api: LanguageAPI,
                          java_api: LanguageAPI) -> int:
    print("# GrowNet API Parity Report")
    print()
    print("**Inputs**")
    print()
    print(f"- C++ root: `{args.cpp_root}`")
    print(f"- Java root: `{args.java_root}`")
    if args.contract_yaml:
        print(f"- Contract YAML: `{args.contract_yaml}` {'(loaded)' if contract_api else '(NOT loaded)'}")
    print()

    diffs_found = 0

    if contract_api:
        print("## 1) C++ vs Contract (v5)")
        print()
        cpp_vs_contract = diff_lang_vs_contract(cpp_api, contract_api)
        for cname in sorted(cpp_vs_contract.keys()):
            row = cpp_vs_contract[cname]
            missing = row.get("missing_in_Cpp", []) or row.get("missing_in_Cp", []) or row.get("missing_in_Cppp", [])
            extra = row.get("extra_in_Cpp", []) or row.get("extra_in_Cp", []) or row.get("extra_in_Cppp", [])
            if missing or extra:
                diffs_found += len(missing) + len(extra)
                print(f"### Class `{cname}`")
                if missing:
                    print(f"- ❗ Missing in C++: {', '.join(missing)}")
                if extra:
                    print(f"- ⚠️  Extra in C++: {', '.join(extra)}")
                print()
        if diffs_found == 0:
            print("- ✅ No differences detected.")
        print()

        print("## 2) Java vs Contract (v5)")
        print()
        java_vs_contract = diff_lang_vs_contract(java_api, contract_api)
        section_diffs = 0
        for cname in sorted(java_vs_contract.keys()):
            row = java_vs_contract[cname]
            missing = row.get("missing_in_Java", [])
            extra = row.get("extra_in_Java", [])
            if missing or extra:
                section_diffs += len(missing) + len(extra)
                print(f"### Class `{cname}`")
                if missing:
                    print(f"- ❗ Missing in Java: {', '.join(missing)}")
                if extra:
                    print(f"- ⚠️  Extra in Java: {', '.join(extra)}")
                print()
        diffs_found += section_diffs
        if section_diffs == 0:
            print("- ✅ No differences detected.")
        print()

    # Java vs C++
    print("## 3) Java ⇄ C++ parity")
    print()
    jvscpp = diff_java_cpp(java_api, cpp_api)
    section_diffs = 0
    for cname in sorted(jvscpp.keys()):
        row = jvscpp[cname]
        mjava = row["missing_in_java"]
        mcpp = row["missing_in_cpp"]
        case_only = row["case_only_mismatches"]
        if mjava or mcpp or case_only:
            section_diffs += len(mjava) + len(mcpp) + len(case_only)
            print(f"### Class `{cname}`")
            if mjava:
                print(f"- ❗ Present in C++ but missing in Java: {', '.join(mjava)}")
            if mcpp:
                print(f"- ❗ Present in Java but missing in C++: {', '.join(mcpp)}")
            if case_only:
                print(f"- ℹ️  Names differ only by case or style (same arity):")
                for p in case_only:
                    print(f"  - {p}")
            print()
    diffs_found += section_diffs
    if section_diffs == 0:
        print("- ✅ Java and C++ public APIs match by name+arity.")
    print()

    # Suggestions (lightweight heuristics)
    print("## 4) Rename suggestions (heuristics)")
    print()
    print("- If you see items like `addInput2DLayer/2` vs `addInputLayer2D/2`, prefer a single canonical name ")
    print("  across both languages (contract v5). Consider adding a thin overload/alias temporarily.")
    print("- For case-only differences (e.g., `tick2D` vs `tick2d`), align to the contract’s spelling exactly.")
    print()

    if args.fail_on_diff and diffs_found > 0:
        return 1
    return 0


# ---------- Main ----------

def main():
    parser = argparse.ArgumentParser(description="GrowNet API parity diff (Java, C++) against v5 contract.")
    parser.add_argument("--cpp-root", required=True, help="Root folder for C++ sources (headers+impl).")
    parser.add_argument("--java-root", required=True, help="Root folder for Java sources.")
    parser.add_argument("--contract-yaml", required=False, default=None, help="Path to GrowNet_Contract_v5_master.yaml.")
    parser.add_argument("--skip-dirs", nargs="*", default=list(DEFAULT_SKIP_DIRS),
                        help="Directory names to skip (any depth).")
    parser.add_argument("--cpp-include-exts", nargs="*", default=list(DEFAULT_CPP_EXTS),
                        help="File extensions to scan for C++.")
    parser.add_argument("--java-include-exts", nargs="*", default=list(DEFAULT_JAVA_EXTS),
                        help="File extensions to scan for Java.")
    parser.add_argument("--fail-on-diff", action="store_true", help="Exit non-zero if any diffs found.")
    args = parser.parse_args()

    skip_dirs = set(args.skip_dirs)
    cpp_exts = set([e.lower().lstrip('.') for e in args.cpp_include_exts])
    java_exts = set([e.lower().lstrip('.') for e in args.java_include_exts])

    # Extract APIs
    cpp_api = extract_cpp_api(args.cpp_root, cpp_exts, skip_dirs)
    java_api = extract_java_api(args.java_root, java_exts, skip_dirs)
    contract_api = _extract_contract_api(args.contract_yaml) if args.contract_yaml else None

    rc = print_markdown_report(args, contract_api, cpp_api, java_api)
    sys.exit(rc)


if __name__ == "__main__":
    main()
