This bundle contains a Codex PR you can run directly against your repo:

Run:
  codex --full-auto exec --dangerously-bypass-approvals-and-sandbox     --model gpt-5-pro --reasoning max     < docs/PR_finish_todos_mojo.md

The PR will:
  - Add `select_anchor_slot_id(...)` to Mojo SlotEngine
  - Refactor Mojo Neuron.on_input(...) to call the selector
  - Ensure SlotConfig knobs exist in Mojo
  - Add <algorithm> include to C++ SlotEngine.cpp (if missing)

No changes to Java/Python in this PR.
