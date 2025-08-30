# PR: Apply Phase A — Temporal Focus via CR YAMLs

You are Codex (GPT-5, max reasoning). Produce **one single, unified diff** for Phase A.

## Context
- CR YAMLs live in `codex/cr/`.
- Apply in this order:
  1) `codex/cr/CR-BOOT.yaml`
  2) `codex/cr/CR-A-01-temporal-slotconfig.yaml`
  3) `codex/cr/CR-A-02-neuron-focus-fields.yaml`
  4) `codex/cr/CR-A-03-slotengine-anchor-logic.yaml`
  5) `codex/cr/CR-A-04-growth-neuron.yaml`
  6) `codex/cr/CR-A-05-tests.yaml`

## What to do
For each YAML above:
- Open the file and strictly follow:
  - `preconditions` → if a precondition fails, STOP and report which one.
  - `actions` → perform anchored/idempotent edits.
  - `postconditions` → verify they now pass.
- Do **not** execute/commit anything locally; just prepare an in-memory diff.
- After all CRs are processed, print a **single unified diff** (git-style patch) to stdout. Do not apply it.

## Constraints & style
- Java is gold semantics; mirror behaviors in other languages when asked.
- Python: snake_case, **no leading `_` on fields**.
- Mojo: `struct` + `fn`, explicit parameter/return types, no clever tricks.
- Do not remove public methods. If changing behavior, keep a delegating alias.
- Respect “ports are edges”; 2D uses `tick_2d` (with `tick_image` delegating), ND uses `tick_nd`.

## Output
- A single unified diff containing all Phase A changes, ready for `codex apply`.
- If anything blocks (precondition mismatch), stop and report precisely which file/pattern failed.

