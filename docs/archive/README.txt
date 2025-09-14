This bundle contains a Codex PR you can run directly against your repo:

Run:
  codex --full-auto exec --dangerously-bypass-approvals-and-sandbox     --model gpt-5-pro --reasoning max     < docs/PR_finish_todos_mojo.md

The PR will:
  - Add `select_anchor_slot_id(...)` to Mojo SlotEngine
  - Refactor Mojo Neuron.on_input(...) to call the selector
  - Ensure SlotConfig knobs exist in Mojo
  - Add <algorithm> include to C++ SlotEngine.cpp (if missing)

No changes to Java/Python in this PR.

More documentation
- Coding Style (MUST READ): docs/CODING_STYLE_MUST_READ.md
- Central changelog index: CHANGELOG.md (links to docs/changelog entries)
- PAL (Parallelism Abstraction Layer): docs/PAL_README.md

Parallelism Abstraction Layer (PAL)
-----------------------------------
PAL provides a unified `parallel_for` / `parallel_map` API across Python, Java, C++, and Mojo with deterministic results. Backends:
- C++: OpenMP (enabled if available via CMake flag `-DGROWNET_WITH_OPENMP=ON`, default ON)
- Java: fixed platform executor + structured orchestration
- Python/Mojo: deterministic sequential façade (CPU tiling in Mojo), safe to adopt now

Feature flag (Python): set `GROWNET_ENABLE_PAL=1` to aggregate structural metrics via PAL in the 2D tick path. Default off; behavior unchanged otherwise.

Benchmarks
----------
For coarse performance comparisons across Python, Java, C++, and Mojo on HD 1920×1080 2D ticks (and Retina/Topographic wiring), see docs/BENCHMARKS.md. A one‑shot driver script exists:

  bash scripts/run_stress_bench.sh

It runs HD and Retina stress tests per language (where toolchains are available) and prints a timing summary table. No strict thresholds are enforced; numbers are informational and vary by machine.
