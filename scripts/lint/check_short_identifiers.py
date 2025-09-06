#!/usr/bin/env python3
import re
import sys
import pathlib


SHORT_VAR_PATTERNS = [
    r"\bfor\s*\(\s*(?:const\s+)?(?:auto|int|size_t|std::size_t)\s+([a-zA-Z]{1,2})\s*=",  # C++ for
    r"\bfor\s*\(\s*int\s+([a-zA-Z]{1,2})\s*=",                                             # Java for
    r"\b([a-zA-Z]{1,2})\s*=\s*[^=]",                                                         # generic assignment
    r"\b([a-zA-Z]{1,2})\s*;",                                                                 # declaration without init
]

ALLOWLIST = {"ok", "id"}


def file_matches(path: pathlib.Path) -> bool:
    return path.suffix in {".cpp", ".cc", ".cxx", ".h", ".hpp", ".java"}


def scan_text(text: str) -> list[str]:
    errors: list[str] = []
    for pattern in SHORT_VAR_PATTERNS:
        for match in re.finditer(pattern, text):
            try:
                name = match.group(1)
            except IndexError:
                continue
            if not name:
                continue
            if name.lower() in ALLOWLIST:
                continue
            if len(name) <= 2:
                errors.append(name)
    return errors


def main() -> int:
    args = [pathlib.Path(p) for p in sys.argv[1:]]
    files = [p for p in args if file_matches(p)]
    bad: dict[str, list[str]] = {}
    for fpath in files:
        try:
            text = fpath.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        ids = scan_text(text)
        if ids:
            bad[str(fpath)] = sorted(set(ids))
    if bad:
        print("Short identifiers found (min length is 3):")
        for fname, names in bad.items():
            print(f"  {fname}: {', '.join(names)}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

