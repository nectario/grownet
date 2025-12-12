#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


@dataclass(frozen=True)
class RefIssue:
    ref: str
    resolved: str
    message: str


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate docs/READ_ORDER.md references exist and avoid docs/archive.")
    parser.add_argument(
        "--read-order",
        default="docs/READ_ORDER.md",
        help="Path to docs/READ_ORDER.md.",
    )
    parser.add_argument(
        "--check-docs-index",
        action="store_true",
        help="Optional: also validate docs/DOCS_INDEX.md references (may be noisy).",
    )
    parser.add_argument(
        "--docs-index",
        default="docs/DOCS_INDEX.md",
        help="Path to docs/DOCS_INDEX.md.",
    )
    return parser.parse_args(argv)


def extract_backtick_refs(markdown_text: str) -> list[str]:
    return re.findall(r"`([^`]+)`", markdown_text)


def looks_like_file_ref(token: str) -> bool:
    if not token:
        return False
    if token.startswith(("http://", "https://")):
        return False
    if "(" in token or ")" in token:
        return False
    if token.endswith("/"):
        return False
    # Heuristic: require a file extension we care about.
    lowered = token.lower()
    return any(lowered.endswith(ext) for ext in (".md", ".json", ".txt", ".sh"))


def resolve_ref(repo_root: Path, docs_root: Path, token: str) -> Path:
    token_stripped = token.strip()
    if token_stripped.startswith("docs/"):
        return repo_root / token_stripped
    if token_stripped.startswith("contracts/"):
        return docs_root / token_stripped
    if token_stripped.startswith(("src/", "tools/", "scripts/")):
        return repo_root / token_stripped
    return docs_root / token_stripped


def validate_markdown_refs(repo_root: Path, markdown_path: Path) -> list[RefIssue]:
    docs_root = repo_root / "docs"
    content = markdown_path.read_text(encoding="utf-8")
    refs = extract_backtick_refs(content)

    issues: list[RefIssue] = []
    for token in refs:
        if not looks_like_file_ref(token):
            continue
        resolved_path = resolve_ref(repo_root, docs_root, token)

        resolved_display = str(resolved_path.as_posix())
        if "docs/archive/" in resolved_display.replace("\\", "/"):
            issues.append(
                RefIssue(ref=token, resolved=resolved_display, message="Reference points into docs/archive (disallowed).")
            )
            continue
        if not resolved_path.exists():
            issues.append(RefIssue(ref=token, resolved=resolved_display, message="Referenced file does not exist."))
            continue
        if not resolved_path.is_file():
            issues.append(RefIssue(ref=token, resolved=resolved_display, message="Referenced path is not a file."))
            continue
    return issues


def emit_issues(title: str, issues: Iterable[RefIssue]) -> None:
    print(title)
    for issue in issues:
        print(f"- {issue.ref} -> {issue.resolved}: {issue.message}")


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    repo_root = Path.cwd()

    read_order_path = repo_root / args.read_order
    if not read_order_path.exists():
        print(f"[FAIL] Missing: {read_order_path}")
        return 1

    issues = validate_markdown_refs(repo_root, read_order_path)

    if args.check_docs_index:
        docs_index_path = repo_root / args.docs_index
        if not docs_index_path.exists():
            issues.append(RefIssue(ref=str(args.docs_index), resolved=str(docs_index_path), message="Missing docs index file."))
        else:
            issues.extend(validate_markdown_refs(repo_root, docs_index_path))

    if issues:
        print("[FAIL] Documentation reference check failed.")
        emit_issues("Issues:", issues)
        return 1

    print(f"[OK] Docs references validated: {read_order_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

