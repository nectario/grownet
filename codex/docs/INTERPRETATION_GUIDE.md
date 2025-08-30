# INTERPRETATION GUIDE — Codex CR YAMLs

The CR YAMLs in this pack use a small, consistent vocabulary:

## Top-level keys
- `meta`: id, title, rerunnable flag, language_targets (optional).
- `preconditions`: checks before running actions (abort if any fails).
- `actions`: ordered steps (edits, inserts, patches, includes, or shell runs).
- `postconditions`: assertions after running actions (warn or fail on mismatch).

## Supported action types (used in this pack)
- `add_file`: create a file with content (skip/overwrite guarded by `if_exists`).
- `ensure_block`: insert a code block before/after an **anchor** pattern if not already present.
- `replace_block`: replace one block delimited by start/end markers (keeps signature where needed).
- `patch_text`: safe search/replace with context (minimize unintended edits).
- `instruction`: free-form instruction for GPT to adapt code where file shapes differ.
- `run`: shell command (build/tests) — non-fatal by default in this pack.
- `include`: chain another YAML (lets you apply `PHASE_A.yaml`, `PHASE_B.yaml`).

## Anchors
Prefer comment anchors in code, e.g.:
```java
// [GROWNET:ANCHOR::AFTER_METRICS]
```
CRs look for anchors to insert code deterministically. When anchors are missing,
the CRs use conservative `anchor_before` and glob matches.

## Idempotency
All CRs are **rerunnable**. `ensure_block` does nothing if the block is already present.

## Guardrails
- Never delete public methods unless replacing with a delegating alias.
- Keep Java/API shapes aligned across C++/Python/Mojo.
- Respect style: Python **no leading `_` in fields**; Mojo uses `struct` + `fn` + typed params; avoid clever tricks.

