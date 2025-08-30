# ONBOARDING — How Codex should familiarize itself with GrowNet

1) **Scan project structure**
   - Expect `src/java`, `src/cpp`, `src/python`, `src/mojo`, and `docs`.
   - If paths differ, adapt globs in CRs accordingly.

2) **Read the core docs (if present)**
   - `docs/contracts/GrowNet_Contract_v3_master.yaml` — API shapes & parity rules.
   - `docs/GrowNet_Design_Spec_v3.md` — architecture, buses, slotting, metrics.
   - `docs/GrowNet_Glossary_v3.1.md` (or similar) — terminology (Region/Layer/Neuron/Slot/Synapse).
   - `docs/codex/CONTEXT_GrowNet_Vision.md` (in this pack) — Temporal/Spatial Focus, growth.

3) **Build sanity (non-fatal in bootstrap)**
   - `mvn -q -DskipTests test` (Java)
   - `cmake -S src/cpp -B build && cmake --build build` (C++)
   - `pytest -q` (Python)
   - Mojo: ensure `fn` + typed params; minimal builds if toolchain is available.

4) **Language style & parity**
   - Java is **gold** for semantics; C++/Python/Mojo mirror behavior.
   - Python: snake_case; fields do **not** start with `_`.
   - Mojo: `struct`, `fn`, explicit typed params; descriptive variable names.
   - Ensure Region API surface: addLayer/connectLayers/bindInput/tick/tick2D/tickND/prune/metrics.

5) **Mental model**
   - **Temporal Focus**: anchor-based slotting; Δ% vs anchor for binning; growth triggers when outlier + capacity.
   - **Spatial Focus**: spotlight mask in shape-aware inputs (2D/ND): top-k + sticky + Gaussian falloff.
   - **Growth ladder**: slot → neuron → layer → region; budgets + cooldowns prevent runaway growth.

6) **When adapting code**
   - Prefer additive changes; avoid removing public methods.
   - If a helper is missing (e.g., `spawnSiblingLike`), add a minimal version with javadoc and TODO.
   - Keep metrics and pulses behavior unchanged unless explicitly instructed.

