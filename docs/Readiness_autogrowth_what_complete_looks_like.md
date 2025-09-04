Based on everything we’ve implemented and discussed so far (slots→neurons→layers→regions, strict slot capacity, fallback streaks, cooldowns, autowiring, and “one growth per tick”), here’s a focused **readiness audit** you can run locally to confirm nothing is missing for **automatic growth at all three levels**. I’ve also included a short **self‑test plan** that will surface any gaps immediately.

------

## What “complete” looks like

For **each language** (Python, C++, Java, Mojo), you should be able to answer **yes** to every item in the matrix:

### A) Slot growth (in‑neuron)

-  **Strict capacity**: Once a neuron is at `slot_limit`, **no new slots** are allocated (both scalar and 2D); selection **reuses** an existing slot deterministically.
-  **Fallback marking**: When selection “wanted a new bin but couldn’t,” the neuron sets a flag (e.g., `last_slot_used_fallback` / equivalent).
-  **Per‑neuron override**: If the neuron has `slot_limit` set, the selector uses that instead of the global cfg.
-  **2D parity**: 2D path follows the same rules: desired bin → out‑of‑domain/at‑capacity → fallback; fallback flag is updated.
-  **Frozen slots**: Freezing a slot prevents its weight/inhibition/modulation updates; **unfreeze** supports a one‑shot “prefer last slot” so the next tick resumes on the intended slot (Python ✅, Java ✅; make sure C++/Mojo also prefer the last slot once).

### B) Neuron growth (in‑layer)

-  **Escalation trigger**: On each input, if the neuron is at capacity **and** the selector flagged fallback, you increment a **fallback streak**.
-  **Threshold + cooldown**: When `fallback_streak ≥ fallback_growth_threshold` and `bus.current_step - last_growth_tick ≥ neuron_growth_cooldown_ticks`, the neuron asks its **owner layer** to add a neuron.
-  **Owner backref**: Every neuron has its `owner` set at construction in **all** layer types (standard Layer, InputLayer2D, OutputLayer2D, ND I/O).
-  **Cloning**: `Layer.try_grow_neuron(seed)` creates a neuron of the **same kind** (E/I/M), applies the seed’s slot policy/limit, and puts it on the **same bus**.
-  **Autowiring (new neuron)**:
  - **Outbound mesh**: replay recorded `connect_layers(src→dst, prob, feedback)` rules: new source → each target with Bernoulli(prob).
  - **Inbound mesh**: replay `src→(new target)` with Bernoulli(prob).
  - **Windowed tracts**: if the growing layer was a **source** in a `connect_layers_windowed`, attach the new source neuron (Python has `attach_source_neuron(new_idx)`; ensure parity or a documented stopgap in C++/Java/Mojo).

### C) Layer growth (in‑region)

-  **Region policy/engine**: End‑of‑tick computes **pressure** (e.g., average slots/neuron, or % of neurons at capacity with fallback streaks) and consults policy:
  - `enable_layer_growth`, `max_layers`, `layer_cooldown_ticks`, and a seeded RNG for determinism.
-  **One growth per tick**: Region grows **at most one layer** per tick when pressure ≥ threshold and cooldown passed.
-  **Spillover layer**: Region adds a small **excitatory‑only** spillover layer (or policy‑driven composition).
-  **Deterministic wiring (new layer)**:
  - Connect **saturated layer → new layer** with **p = 1.0** (deterministic fan‑out) unless a different p is explicitly configured.
  - Optional: duplicate inbound mesh rules into the new layer (documented if deferred).
-  **RNG determinism**: Wiring uses a region‑level RNG with a fixed seed.
-  **Metrics/logging**: Region can report “grew N neurons / 1 layer this tick” so tests and demos can assert behavior.

### D) Buses & ticks

-  **Bus step**: `LateralBus` (and `RegionBus` if present) increments a **monotonic step counter** at end‑of‑tick and exposes `get_current_step()`/`getStep()`; neurons use it for growth cooldown.
-  **Two‑phase tick**: Forward pass (deliver and fire) → **end‑of‑tick** (decay buses, run growth policy). Region‑level growth is after all layers end their ticks.

### E) Demos, tests, docs

-  **Demos**: A small “aggressive growth” demo that shows: (1) slots saturate → neuron count increases; (2) neurons saturate → region adds a layer.
-  **Unit tests**:
  - slot strict‑cap (scalar & 2D)
  - neuron fallback streak → growth + cooldown
  - autowiring smoke (mesh + windowed)
  - region pressure → single layer growth per tick; cooldown respected
-  **Docs**: `GROWTH.md` explains all three levels with knobs and short “enable it” snippets for Python/C++/Java/Mojo.

------

## Fast local self‑test plan (what to run)

> **Goal:** if any part is missing, these will fail or produce obviously wrong counts.

1. **Slot strict‑cap (2D)**

- Construct a 2D input → hidden layer with each hidden neuron `slot_limit = 1`.
- Drive a moving dot that lands in a **new** bin each tick.
- **Expect:** number of slots per neuron never exceeds **1**; `last_slot_used_fallback == True` when a new bin was desired.

1. **Neuron growth**

- Use the same setup and set per‑neuron `fallback_growth_threshold = 1`, `neuron_growth_cooldown_ticks = 0`.
- **Expect:** hidden layer neuron count **increases** within a few ticks; new neuron is **auto‑wired** (can observe downstream activity).

1. **Region growth**

- Add `neuron_limit` on the hidden layer; set `enable_layer_growth = True`, `max_layers ≥ current+1`, `layer_cooldown_ticks = 0`, and a **low** pressure threshold.
- **Expect:** after neurons hit the cap and the dot keeps moving, the region adds **exactly one new layer**; wiring from saturated → new has probability **1.0** (all edges present).

1. **Windowed tracts smoke**

- Connect Input2D → Hidden via windowed helper.
- After growth, ensure newly grown **source** neurons deliver events downstream (Python: `attach_source_neuron(new_idx)` path exercised).
- For languages where tract re‑attachment isn’t implemented yet, ensure it’s **documented** or add a stopgap (e.g., persistent direct edges) so behavior is still correct.

1. **Cooldown and determinism**

- Repeat tests with `layer_cooldown_ticks > 0` and a fixed RNG seed.
- **Expect:** at most **one** region‑level growth per tick; run twice with same seed yields identical wiring topology.

------

## Common “last‑mile” gaps to check

These are the usual places where a single missing line prevents growth parity:

1. **C++ & Java 2D fallback marking**
    Ensure `selectOrCreateSlot2D` (or your 2D path) sets the **fallback flag** used by the neuron’s growth logic, not just the scalar path.
2. **Prefer‑last‑slot‑once after unfreeze (C++/Mojo)**
    Python and Java handle this; add a `preferLastSlotOnce` boolean so the next selection can reuse the intended slot exactly once after unfreezing.
3. **Tract re‑attachment parity (C++/Java/Mojo)**
    Python has `attach_source_neuron(new_idx)` for windowed tracts. If C++/Java/Mojo don’t, either:
   - implement an equivalent subscription, **or**
   - ensure the growth path for those languages uses persistent edges that make the new neuron’s output reach the same destinations.
4. **Region growth wiring probability**
    Standardize on **p = 1.0** from saturated → new layer (unless your policy says otherwise). We’ve used 0.15 in some earlier drafts; flip to 1.0 for deterministic spillover unless there’s a reason not to.
5. **One growth per tick guard**
    Confirm the region‑engine checks and enforces “**≤ 1 layer grown in this tick**.”
6. **Owner backrefs on all layer types**
    It’s easy to set `owner` in the main `Layer` constructor but forget it in `InputLayer2D`, `OutputLayer2D`, and `InputLayerND`. Verify all languages.
7. **Bus step exposure**
    Make sure `LateralBus` (and `RegionBus` if used) expose `get_current_step()`/`getStep()` **and** are actually called in each layer’s `end_tick()` so cooldown math works.
8. **Docs + examples**
    `GROWTH.md` should include a short “turn it on” snippet per language (knobs + tiny demo), and a paragraph describing region‑level triggers and the invariant “one growth per tick.”

------

## If you want a tiny “polish” PR after your review

If any box above is unchecked, I suggest a minimal patch that:

- Standardizes **p = 1.0** for saturated→new layer wiring in region growth.
- Adds a **preferLastSlotOnce** flag to C++/Mojo (set on unfreeze; respected in the next selection).
- Ensures **2D fallback flag** is updated in C++/Java selectors.
- Adds a **`tests/test_region_growth.\*`** (Python and one compiled language) exercising:
  - slot strict‑cap,
  - neuron growth on fallback,
  - single layer growth per tick.

I’m happy to produce an exact diff once you confirm which of the above you want to change. If your local run shows a failure in any of the five self‑tests, tell me which step failed (and the language), and I’ll give you a laser‑focused patch for that module.