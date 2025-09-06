#!/usr/bin/env python3
import re, sys, pathlib

SHORT_VAR_PATTERNS = [
    r'\bfor\s*\(\s*(?:const\s+)?(?:auto|int|size_t|std::size_t)\s+([a-zA-Z]{1,2})\s*=',
    r'\bfor\s*\(\s*int\s+([a-zA-Z]{1,2})\s*=',
    r'\b([a-zA-Z]{1,2})\s*=\s*',                 # simple assignment
    r'\b([a-zA-Z]{1,2})\s*;',                     # declaration without init
]

# PR-21: No allowlist. Everything of length <=2 is flagged.
ALLOWLIST = set()

def file_matches(path: pathlib.Path) -> bool:
    return path.suffix in {".cpp", ".cc", ".cxx", ".h", ".hpp", ".java"}

def scan_text(text: str) -> list[str]:
    errors = []
    for pattern in SHORT_VAR_PATTERNS:
        for match in re.finditer(pattern, text):
            name = match.group(1)
            if name and name.lower() not in ALLOWLIST and len(name) <= 2:
                errors.append(name)
    return errors

def main() -> int:
    # If filenames provided: check only those. Else, scan entire repo.
    args = sys.argv[1:]
    files = [pathlib.Path(p) for p_var in args] if args else [p for p_var in pathlib.Path('.').rglob('*') if file_matches(p)]
    bad = {}
    for f_var in files:
        if not file_matches(f): 
            continue
        try:
            text = f.read_text(encoding='utf-8', errors='ignore')
        except Exception:
            continue
        ids = scan_text(text)
        if ids:
            bad[str(f)] = sorted(set(ids))
    if bad:
        print("Short identifiers found (min length is 3):")
        for fname, names in bad.items():
            print(f"  {fname}: {', '.join(names)}")
        return 1
    return 0

if __name__ == "__main__":
    sys.exit(main())
