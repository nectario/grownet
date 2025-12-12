# Session Worklog — 2025‑09‑03

This changelog summarizes all code and docs changes implemented today across Python, Mojo, C++, and Java, with a focus on parity, readability, spatial metrics, demos, and automatic region growth (layers → region).

---

## Highlights

- Added automatic region growth (Layers → Region) with policy controls and deterministic wiring.
- Brought Mojo implementation into 1‑for‑1 parity with Python where applicable (typed `fn/struct`, strict capacity, fallback marking, end‑of‑tick hooks).
- Added/updated demos for spatial focus and spatial metrics; improved code readability by replacing short variable names.
- Extended docs (growth and quick start) and added tests.

---

## Python

- Region Growth
  - Added `src/python/growth.py` with:
    - `GrowthPolicy` knobs (enable_layer_growth, max_total_layers, avg_slots_threshold, percent_neurons_at_cap_threshold, layer_cooldown_ticks, new_layer_excitatory_count, wire_probability).
    - `maybe_grow(region, policy)`: end‑of‑tick layer growth if pressure and cooldown allow; adds an E‑only spillover layer and wires saturated → new.
  - Integrated into `src/python/region.py`:
    - New fields: `growth_policy`, `last_layer_growth_step`.
    - Helpers: `set_growth_policy(policy)`, `get_growth_policy()`.
    - Hooks: call `maybe_grow(...)` at the end of `tick(...)` and `tick_2d(...)` (after `end_tick`/decay and metric aggregation).

- Spatial Focus / Metrics / Readability
  - `src/python/region.py`:
    - Renamed short variables to descriptive ones in windowed wiring and spatial metrics (e.g., `source_height`, `kernel_height`, `window_origins`, `chosen_frame`, `outgoing_list`).
    - Spatial metrics prefer last `OutputLayer2D` frame except when all‑zero (then fall back to input).

- Tests
  - Added `src/python/tests/test_region_growth.py` to assert that a region adds a new layer under aggressive growth policy.

---

## Mojo

- Parity & Strictness
  - Updated `src/mojo/slot_engine.mojo`, `src/mojo/neuron.mojo`, `src/mojo/layer.mojo`, `src/mojo/region.mojo` to mirror Python semantics:
    - Strict slot capacity (scalar and 2D) with deterministic fallback reuse; `last_slot_used_fallback` marking.
    - Growth bookkeeping (`fallback_streak`, `last_growth_tick`) and per‑layer escalation in `end_tick` with cooldown via bus `current_step`.
    - Region holdbacks and autowiring for grown neurons via mesh rules replay.
    - Replaced all `let` with `var` and typed all params; no leading underscores.

- Spatial Metrics & Demos
  - `src/mojo/region.mojo`: `tick_2d` computes spatial metrics; prefers last `OutputLayer2D` frame and falls back to input when needed.
  - Demos:
    - `src/mojo/image_io_demo.mojo`: prints delivered events and spatial metrics with `region.enable_spatial_metrics = True`.
    - New `src/mojo/spatial_focus_demo.mojo`: windowed wiring + spatial slotting; prints delivered, active pixels, centroid, bbox, unique windowed source count.

- Automatic Region Growth (Layers → Region)
  - Added `src/mojo/growth_policy.mojo` and `src/mojo/growth_engine.mojo`.
  - Integrated into `src/mojo/region.mojo`: fields `growth_policy`, `growth_policy_enabled`, `last_layer_growth_step`; `set_growth_policy/get_growth_policy` helpers; `maybe_grow(...)` hook at end of `tick`/`tick_2d`.

---

## C++

- Growth Policy & Engine Hook
  - Added `src/cpp/GrowthPolicy.h` with GrowthPolicy knobs aligning with other languages.
  - `src/cpp/Region.h`:
    - Included `GrowthPolicy.h`.
    - Added overload `int requestLayerGrowth(Layer* saturated, double connectionProbability)`.
    - Added policy API: `setGrowthPolicy`, `getGrowthPolicy`, and `maybeGrowRegion()` declaration.
    - New state: `growthPolicy`, `hasGrowthPolicy`, `lastRegionGrowthStep`.
  - `src/cpp/Region.cpp`:
    - Implemented overloaded `requestLayerGrowth`.
    - Added end‑of‑tick calls to `maybeGrowRegion()` in `tick(...)` and `tickImage(...)`.
    - Implemented `maybeGrowRegion()` with per‑layer pressure scan and deterministic spillover wiring.

- Spatial Metrics parity in `tickImage(...)` maintained (prefer OutputLayer2D frame; fallback to input if needed).

---

## Java

- Region Growth Integration
  - `Region.java`: at end of `tick(...)` and `tick2D(...)` now calls `GrowthEngine.maybeGrow(...)` (in addition to existing neuron growth), enabling automatic region layer growth under policy.
  - Added overloaded `requestLayerGrowth(Layer saturated, double connectionProbability)` to use policy’s wiring probability.

- Demo & Test
  - Added `RegionGrowthDemo.java` to exercise region growth under aggressive policy and print layer counts.
  - Added JUnit test `RegionGrowthTest.java` asserting growth after a few frames.
  - `pom.xml`: added a `region-growth-demo` profile to run the demo via `mvn -q -Pregion-growth-demo exec:java`.

---

## Docs

- `docs/README.md`: added Mojo demos (image I/O and spatial focus) and spatial metrics notes.
- `docs/GrowNet_Quick_Start_for_Engineers.md`: added “Mojo Demos (CLI)” section and metrics notes.
- `docs/GROWTH.md`: added “Region Growth (automatic layer creation)” section (triggers, safety, action, and enable example).

---

## Code Style & Readability

- Variable names: replaced ambiguous single/double‑character names with descriptive ones (excluding short loop counters like i/j where appropriate).
- No leading underscores in new symbols.
- Mojo: removed all `let` usage; `var` only; all functions typed; `struct` used instead of inheritance where practical.
- Determinism: growth and wiring use the region’s RNG and/or deterministic wiring helpers.

---

## Known Follow‑ups

- Optional: mirror Region growth policy to a distinct Python growth_policy.py / growth_engine.py split if desired (current code keeps both in `growth.py` for simplicity).
- Optional C++ unit tests mirroring the Python/Java growth tests.
- Minor cleanup: remove stray duplicate prototype at the bottom of `src/cpp/Region.h` (non‑functional duplication from prior revisions).

