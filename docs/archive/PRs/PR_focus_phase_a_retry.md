# PR: Apply Phase A (retry) — Bootstrap + Temporal Focus via CR YAMLs

You are Codex (GPT-5, max reasoning). Produce **one unified diff**, do not apply.

## Order
1) codex/cr/CR-A-04a-bootstrap-growth.yaml
2) codex/cr/CR-A-02-python-path-fix.yaml
3) codex/cr/CR-BOOT.yaml
4) codex/cr/CR-A-01-temporal-slotconfig.yaml
5) codex/cr/CR-A-02-neuron-focus-fields.yaml   # Java/C++/Mojo parts only; Python already handled above.
6) codex/cr/CR-A-03-slotengine-anchor-logic.yaml
7) codex/cr/CR-A-04-growth-neuron.yaml
8) codex/cr/CR-A-05-tests.yaml

## Rules
- For each YAML: respect preconditions → actions → postconditions.
- Adapt globs as needed; do not remove public methods.
- Output a single git-style unified diff (do not apply).

