# Coding Style (MUST READ)

This repository spans Python, Mojo, C++, and Java with strong cross‑language parity. The goal is small, clear, deterministic code with consistent naming and end‑of‑tick semantics. Please follow the rules below.

---

## Global Principles

- Clarity first: prefer descriptive names over brevity. Avoid single/double‑letter identifiers (i, j in loops are acceptable).
- Determinism: when randomness matters (wiring, growth), use the Region’s RNG with a fixed seed and a single code path.
- Parity: public APIs and behavior should match across languages (surface names may vary by idiom).
- No leading underscores in new public symbols. Keep visibility clear through package/namespace/module structure.
- Two‑phase tick discipline: Phase A (inject + local routing), Phase B (tract flush / finalize outputs), then bus decay and structural aggregation.
- Do not throw into tick paths for best‑effort hooks (growth/pruning); swallow locally and continue.

---

## Python

- Naming: snake_case for functions, methods, and variables; PascalCase for classes.
- Imports: local imports are allowed where needed to avoid cycles; keep them at the top when possible.
- Readability: prefer explicit names like `source_height`, `kernel_width`, `window_origins`, `chosen_frame`, `outgoing_list`.
- Slot/Neuron/Layer/Region:
  - Strict slot capacity; mark `last_slot_used_fallback` when fallback is used.
  - Growth: neuron growth in `Layer.end_tick`; region growth after end‑of‑tick aggregation and bus decay.
- Avoid magic numbers; centralize defaults in config/policy types (e.g., SlotConfig, GrowthPolicy).
- Tests: keep them small, deterministic, and end‑to‑end when possible; prefer no network or disk I/O.

---

## Mojo

- Use `struct` and `fn` with typed parameters and return types.
- Use `var`; avoid `let` (not supported in current toolchain).
- Match Python behavior 1‑to‑1:
  - `on_input(value)` and `on_input_2d(value, row, col)` (no external modulation parameter).
  - `SlotEngine.select_or_create_slot` and `_2d` have strict capacity with deterministic fallback and set `last_slot_used_fallback`.
- Layer.end_tick performs neuron growth escalation using `bus.get_current_step()` for cooldown; Region handles layer growth at the end of tick.
- Region spatial metrics prefer last OutputLayer2D’s frame; fall back to input if output is all zeros.
- Avoid single/double‑letter identifiers; use `source_layer`, `dest_layer`, `source_neurons`, `edge_count`, etc.

---

## C++

- Use descriptive names and RAII. Keep headers light; implement logic in .cpp files.
- Region growth:
  - Keep policy in `GrowthPolicy.h`; add setters/getters on Region.
  - Call `maybeGrowRegion()` at the end of tick methods, after `endTick()` and `bus.decay()`.
- Deterministic wiring: use the existing `connectLayers` path and Region RNG.
- Keep `const` correctness and prefer references to raw pointers where safe (existing code uses pointers for layers/neurons; follow local style).

---

## Java

- Use camelCase for methods/fields, PascalCase for classes.
- Region growth hooks belong at the end of tick methods.
- Overloads like `requestLayerGrowth(Layer,double)` should coexist with legacy forms for compatibility.
- Keep demos in `main/java` and tests in `test/java`; prefer JUnit 5.

---

## Growth Semantics

- Slots → Neurons → Layers → Region (escalation order).
- Slot growth happens intra‑neuron only. Neuron growth happens inside a layer and uses region mesh rules for autowiring. Region growth adds new layers; it never creates neurons or slots directly.
- Cooldowns use tick counters (bus `current_step`/`getCurrentStep()`), never wall‑clock.

---

## Spatial Metrics

- Compute spatial metrics in 2D ticks after layer end_tick and bus decay when enabled.
- Prefer last `OutputLayer2D` frame for metrics; if it is all zeros but the input has activity, fall back to the input frame.

---

## Demos & Docs

- Keep minimal demos runnable in each language; prefer printing a small, stable set of metrics.
- Update README and Quick Start when demo behavior changes (e.g., spatial metrics toggle).

---

## Patches & PRs

- Keep patches focused; avoid unrelated refactors.
- Use clear commit messages / PR titles; describe what changed and why.
- Add or update tests and docs as part of the same PR when behavior changes.



**Rule:** No single- or double-character identifiers anywhere, including loops.
