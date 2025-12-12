# GrowNet — What This Codebase Is About

GrowNet is an event‑driven, neuron‑centric research codebase. Neurons don’t hold a single scalar “activation” with a bias; instead, each neuron manages a set of *slots* that specialize to different input regimes over time. Learning is local (no backprop), and capacity can grow as distributions drift. Cross‑language implementations (Python, C++, Java, Mojo, TypeScript, and Rust) expose nearly identical public APIs around regions, layers, neuron types, lateral buses, and shape‑aware I/O. 

------

## Core ideas (at a glance)

- **Neuron as a mini‑system.** Each neuron maintains a map `slot_id → Weight`. Slot thresholds adapt toward a target firing rate while strengths are reinforced on hits.
- **Two‑phase tick.** A region injects input and performs local routing, then flushes inter‑layer delivery and finally decays per‑layer buses—keeping timing semantics stable and feedback well‑behaved.
- **Lateral control.** Each layer’s `LateralBus` carries transient **inhibition** and **modulation** that influence slot reinforcement/thresholding; buses decay at end‑of‑tick.
- **Temporal Focus (V4).** Slot selection uses **FIRST‑anchor** binning (percent‑delta from the first “anchor” observation) to avoid “drift to last value” on monotonic ramps.
- **Growth hooks.** When a neuron saturates (`slot_limit`) yet continues to see outlier inputs, hooks are available to grow capacity (slots/neurons/layers) safely. 

------

## Architecture & data flow

- **Region** owns layers, port bindings (“ports as edges”), wiring helpers, ticks, and pruning. Scalar ticks drive a 1‑neuron edge; 2D ticks drive an `InputLayer2D` edge.
- **Layer** mixes excitatory/inhibitory/modulatory neurons that share a `LateralBus`. `forward(value)` drives neurons; `end_tick()` does housekeeping and bus decay.
- **Neuron** exposes `on_input(value) -> fired` and `on_output(amplitude)`, holds slots + outgoing synapses, and maintains Temporal Focus state (anchor/locks).
- **SlotEngine / SlotConfig** implement slot selection (and creation) with configurable bin widths, epsilon scales, and limits.
- **Shape‑aware I/O**: `InputLayer2D` and `OutputLayer2D` handle grid‑shaped signals; the ND path is scaffolded and extended in Phase B. 

------

## What’s new since V4 (high‑level)

> These items summarize recent changes layered on the original V4 spec.

1. **Spatial Focus (Phase B, Python reference; C++ parity)**
   - **2D slotting.** When enabled on the *receiving* neurons, slot keys become `(row_bin, col_bin)` using per‑axis percent deltas from a 2D anchor (FIRST/ORIGIN), with per‑axis bin widths.
   - **Windowed, deterministic wiring.** `connect_layers_windowed(src2D, dst, kh, kw, sh, sw, padding)` slides a kernel over the input:
     - If `dst` is `OutputLayer2D`: each window wires all source pixels to the **center** output neuron (center = `floor(k/2)` per axis; clamped).
     - Otherwise: each source pixel that appears in any window deterministically participates in delivery (Python uses a 2D‑context fan‑out; C++ currently does a persistent fan‑out to all dst neurons as a stopgap).
   - **Return semantics.** The function returns the number of **unique source subscriptions** (distinct source pixels that participate in ≥1 window), not raw `(src,dst)` edge count.
   - **Spatial metrics (opt‑in).** With `GROWNET_ENABLE_SPATIAL_METRICS=1` (or a per‑region flag), `tick_2d` computes:
      `active_pixels`, `(centroid_row, centroid_col)`, and `bbox=(row_min,row_max,col_min,col_max)`. It prefers the last `OutputLayer2D` frame this tick and falls back to the input frame if needed.
2. **Frozen slots (experimental, opt‑in)**
   - Any slot can be **frozen**: reinforcement and threshold adaptation are disabled for that slot, stabilizing a learned template while other slots continue to adapt.
   - Typical policies: manual freeze, confidence freeze (after N consecutive wins), or stabilization freeze (no drift for M ticks).
   - Unfreezing is symmetric and re‑enables learning on that slot.
3. **Unified bus decay semantics**
   - Across languages, end‑of‑tick performs **multiplicative inhibition decay** (default ~0.90) and **resets modulation** to 1.0. Java gained an `inhibitionDecay` knob for parity.
4. **Parity & clarity**
   - Java `Neuron.onInput` now uses the V4 **anchor** slotter by default (`selectOrCreateSlot`).
   - Variable names were expanded (e.g., `a/b` → `src_neuron/dst_neuron`) for readability; concise in‑code comments/docstrings were added where intent benefits.
5. **Compatibility shims & docs**
   - `GROWNET_COMPAT_DELIVERED_COUNT=bound` (Python tests) preserves a legacy interpretation of `deliveredEvents` in targeted cases.
   - `SPATIAL_FOCUS.md` documents windowed wiring, center rules (even kernels, `"same"` padding), return semantics, and demo instructions.

------

## Slots & learning (with frozen slot support)

- **Temporal slotting (scalar).**
   The engine computes a bin ID from the *percent delta* between the current input and the anchor (FIRST), using `bin_width_pct` and `epsilon_scale`. The selected slot is created on demand (subject to `slot_limit`) and reinforced; its threshold (θ) adapts via EMA to approach target firing rates.
- **Spatial slotting (2D).**
   When `spatial_enabled` is set on the destination neuron’s `slot_cfg`, the engine computes `(row_bin, col_bin)` from `(Δrow, Δcol)` as percent deltas relative to the 2D anchor (FIRST/ORIGIN), with per‑axis bin widths. Capacity is clamped per axis; at saturation, the Python reference reuses a fixed fallback bin.
- **Frozen slots.**
   A slot marked **frozen** is excluded from reinforcement and threshold updates during ticks; `Weight.update_threshold` short‑circuits and returns a “no‑update” decision for that slot. This protects stable templates from drift when modulation/inhibition fluctuates.

------

## Buses & control

Each layer’s `LateralBus` contributes **modulation** (scales learning) and **inhibition** (suppresses activity) and is decayed in `end_tick()`. The unified rule is:

- `inhibitionFactor *= inhibitionDecay` (e.g., 0.90),
- `modulationFactor = 1.0`.

Inhibitory/modulatory neurons *pulse* these factors rather than emitting downstream spikes; excitatory neurons propagate on fire.

------

## Shape‑aware I/O & windowed wiring

- **Ports as edges.** Binding a scalar creates a 1‑neuron input edge; binding a 2D port creates/reuses an `InputLayer2D` edge. Regions remain decoupled from payload shapes. 
- **Deterministic windowed wiring.**
   `connect_layers_windowed` slides a kernel over the input grid with `padding ∈ {valid, same}` and stride `(sh, sw)`:
  - **Center rule (even kernels).** When `kh` or `kw` is even and `padding="same"`, the “center” is `r0 + kh // 2`, `c0 + kw // 2` (floored) and clamped into image bounds.
  - **Return value.** The function returns the number of **unique source pixels** that participate in ≥1 window, independent of how many downstream edges are created.

------

## Metrics & observability

- **Always‑on:** `delivered_events`, `total_slots`, `total_synapses`.
- **Spatial (opt‑in):** `active_pixels`, `(centroid_row, centroid_col)`, and `bbox` (plus camelCase aliases for parity). Enable via `Region.enable_spatial_metrics = True` or `GROWNET_ENABLE_SPATIAL_METRICS=1`. Python computes these on the last `OutputLayer2D` (or input frame fallback); C++ mirrors the same choice in `tickImage`.

------

## Language parity (quick matrix)

| Area                             | Python                        | C++                                                   | Java                     | Mojo         |
| -------------------------------- | ----------------------------- | ----------------------------------------------------- | ------------------------ | ------------ |
| Temporal Focus (FIRST anchor)    | ✅                             | ✅                                                     | ✅ (V4 default)           | ⚙️ stubbed    |
| Spatial slotting (2D)            | ✅ (reference)                 | ⚙️ partial (metrics; windowed wiring; generic fan‑out) | ➖ pending                | ⚙️ stubs      |
| Windowed wiring                  | ✅ (`connect_layers_windowed`) | ✅ (`connectLayersWindowed`; deterministic)            | ➖ pending                | ⚙️ stub       |
| Spatial metrics                  | ✅ (opt‑in)                    | ✅ (opt‑in)                                            | ➖ pending                | ➖            |
| Frozen slots                     | ✅ (API + tests)               | ✅ (API)                                               | ✅ (API + tests)          | ✅ (API)      |
| Bus decay rule                   | ✅ unified                     | ✅ unified                                             | ✅ unified (configurable) | ⚙️ align soon |
| Ports‑as‑edges                   | ✅                             | ✅                                                     | ✅                        | ✅            |
| Back‑compat deliveredEvents shim | ✅ (env‑gated in tests)        | ➖                                                     | ➖                        | ➖            |

> ✅ implemented · ⚙️ partial/stub · ➖ not yet

------

## How to run (Python reference)

- **Classic:**

  ```bash
  PYTHONPATH=src/python python -m src.python.demos.region_demo
  PYTHONPATH=src/python python -m src.python.demos.image_io_demo
  ```

- **Spatial focus demo:**

  ```bash
  PYTHONPATH=src/python python src/python/demos/spatial_focus_demo.py
  # Optional spatial metrics:
  export GROWNET_ENABLE_SPATIAL_METRICS=1
  ```

------

## Testing & developer flags

- **PyTests:** unit tests cover slot formation, image path, Temporal Focus, Spatial Focus (slotting, windowed wiring semantics), and spatial metrics.
- **Compatibility:**
  - `GROWNET_COMPAT_DELIVERED_COUNT=bound` (tests only) — count delivered events by bound layers for legacy expectations.
  - `GROWNET_ENABLE_SPATIAL_METRICS=1` — compute spatial metrics in `tick_2d`.

------

## Roadmap (near‑term)

- **C++/Java Spatial Focus:** bring 2D‑context fan‑out (per‑neuron `onInput2D`) to parity with Python; add tests mirroring Python coverage.
- **Slot capacity policies:** configurable LRU/round‑robin for saturated spatial bins (today: fixed fallback bin in Python).
- **Selective gating parity:** optional per‑edge weight gating during propagation (Java‑style) as a toggle in Python/C++.

------

## Why this matters

GrowNet is a pragmatic, biologically inspired substrate for *local* learning, temporal and spatial attention, and dynamic capacity—all without backprop. The codebase gives you aligned multi‑language references, crisp timing semantics, and tools (tests, demos, metrics) to inspect behavior as you iterate. The current Phase‑B features (Spatial Focus, windowed wiring, spatial metrics, frozen slots) push toward robust spatiotemporal representations while keeping defaults conservative and backwards‑friendly. 

------

*This document supersedes and extends the earlier overview, integrating Phase‑B additions and parity notes. For deeper API signatures and rationale, see the design/spec docs referenced in the repo.* 