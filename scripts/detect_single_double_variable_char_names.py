#!/usr/bin/env python3
# tools/check_short_identifiers_py_mojo.py
import argparse, ast, os, re, sys
from dataclasses import dataclass

ALLOW = set()  # e.g., {"id","ok"} if you really want exceptions; empty keeps the “no 1–2 char” rule strict.

# ---------- Python ----------
@dataclass
class PyHit:
    path: str
    line: int
    name: str
    context: str

def scan_python(root: str) -> list[PyHit]:
    hits: list[PyHit] = []
    for dirpath, _, files in os.walk(root):
        for f in files:
            if not f.endswith(".py"): continue
            path = os.path.join(dirpath, f)
            try:
                src = open(path, "r", encoding="utf-8", errors="ignore").read()
                tree = ast.parse(src, filename=path)
            except Exception:
                continue

            class Visitor(ast.NodeVisitor):
                def visit_FunctionDef(self, node: ast.FunctionDef):
                    # parameters
                    for arg in node.args.args + node.args.kwonlyargs:
                        n = arg.arg
                        if is_short(n): hits.append(PyHit(path, node.lineno, n, f"param of {node.name}"))
                    if node.args.vararg and is_short(node.args.vararg.arg):
                        hits.append(PyHit(path, node.lineno, node.args.vararg.arg, f"*args of {node.name}"))
                    if node.args.kwarg and is_short(node.args.kwarg.arg):
                        hits.append(PyHit(path, node.lineno, node.args.kwarg.arg, f"**kwargs of {node.name}"))
                    self.generic_visit(node)

                def visit_Assign(self, node: ast.Assign):
                    # simple names on LHS
                    for t in node.targets:
                        for n in _lhs_names(t):
                            if is_short(n): hits.append(PyHit(path, getattr(node, "lineno", 0), n, "local assign"))
                    self.generic_visit(node)

                def visit_For(self, node: ast.For):
                    for n in _lhs_names(node.target):
                        if is_short(n): hits.append(PyHit(path, getattr(node, "lineno", 0), n, "for-loop index"))
                    self.generic_visit(node)

            Visitor().visit(tree)
    return hits

def _lhs_names(node):
    names = []
    if isinstance(node, ast.Name):
        names.append(node.id)
    elif isinstance(node, (ast.Tuple, ast.List)):
        for elt in node.elts:
            names.extend(_lhs_names(elt))
    return names

# ---------- Mojo (lightweight) ----------
MOJO_VAR_DEF = re.compile(r'^\s*(?:let|var)\s+([A-Za-z_][A-Za-z0-9_]*)\s*:', re.MULTILINE)
MOJO_FN_DEF  = re.compile(r'^\s*fn\s+([a-z_][a-z0-9_]*)\s*\((.*?)\)\s*->?', re.MULTILINE | re.DOTALL)

@dataclass
class MojoHit:
    path: str
    line: int
    name: str
    context: str

def scan_mojo(root: str) -> list[MojoHit]:
    hits: list[MojoHit] = []
    for dirpath, _, files in os.walk(root):
        for f in files:
            if not f.endswith(".mojo"): continue
            path = os.path.join(dirpath, f)
            try:
                src = open(path, "r", encoding="utf-8", errors="ignore").read()
            except Exception:
                continue
            # var/let
            for m in MOJO_VAR_DEF.finditer(src):
                name = m.group(1)
                line = src.count("\n", 0, m.start()) + 1
                if is_short(name): hits.append(MojoHit(path, line, name, "var/let"))
            # fn params
            for fm in MOJO_FN_DEF.finditer(src):
                params = fm.group(2) or ""
                line = src.count("\n", 0, fm.start()) + 1
                if params.strip():
                    for p in [p.strip() for p in params.split(",") if p.strip()]:
                        # param format: name: Type
                        nm = p.split(":", 1)[0].strip()
                        if is_short(nm): hits.append(MojoHit(path, line, nm, f"param of {fm.group(1)}"))
    return hits

# ---------- Shared ----------
def is_short(name: str) -> bool:
    if name.startswith("_"):  # private is allowed to be short
        return False
    if name in ALLOW:
        return False
    # one or two characters ⇒ fail (strict policy)
    return (len(name) <= 2)

def main():
    ap = argparse.ArgumentParser(description="Find 1–2 char variable/param names in Python & Mojo")
    ap.add_argument("--python-root", default="src/python", help="Python root")
    ap.add_argument("--mojo-root",   default="src/mojo",   help="Mojo root")
    args = ap.parse_args()

    py_hits = scan_python(args.python_root)
    mj_hits = scan_mojo(args.mojo_root)

    total = 0
    if py_hits:
        print("## Python short identifiers")
        for h in py_hits:
            print(f"{h.path}:{h.line}: `{h.name}` — {h.context}")
        total += len(py_hits)
    if mj_hits:
        print("\n## Mojo short identifiers")
        for h in mj_hits:
            print(f"{h.path}:{h.line}: `{h.name}` — {h.context}")
        total += len(mj_hits)

    if total == 0:
        print("✅ No 1–2 character identifiers found in Python/Mojo (public/protected).")
        return 0
    print(f"\n❌ Found {total} short identifiers. Please rename to descriptive names.")
    return 1

if __name__ == "__main__":
    sys.exit(main())
