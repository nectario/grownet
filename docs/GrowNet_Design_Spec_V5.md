# GrowNet Design Specification — V5 (Merged Master)

Status: Candidate for master (merges V5 + V5_second)
Date: 2025‑09‑04
Scope: Core data plane (Region/Layer/Neuron/Slot), Focus (Temporal + 2D), Frozen Slots, Growth (Slots → Neurons → Layers → Regions), two‑phase ticking, deterministic windowed wiring (tracts), cross‑language parity (Python = C++ = Java = Mojo).

What changed from V4
- Anchor‑based Temporal Focus retained and clarified (FIRST mode).
- Frozen slots formalized with unfreeze “prefer last slot once”.
- Strict slot capacity: no new slot allocations at capacity; fallback is marked for growth pressure.
- Automatic growth across Slots → Neurons → Layers → Regions with cooldowns and deterministic re‑wiring.
- Windowed wiring semantics and return value (unique source subscriptions) specified; center rule for SAME/VALID.
- Two‑phase tick timings and bus decay/step counter codified.

---

## 1) Goals & Non‑Goals

Goals
- Deterministic, minimal primitives that grow capacity by escalating the smallest necessary unit.
- Clear, reproducible behavior across Python, C++, Java, Mojo (idiomatic naming per language).
- Two‑phase ticks with bus decay and a monotonic step counter for cooldowns/metrics.
- Deterministic tract/windowed wiring with re‑attachment after growth.

Non‑Goals (V5)
- Advanced learning rules (Hebbian variants, STDP), rich modulation chemistry.
- Distributed execution or multi‑region orchestration.
- Full ND focus operations (ND layers exist; ND tick is staged next).

---

## 2) Core Model

Region
- Owns Layers, port bindings, wiring helpers, tick orchestration, growth policy/engine.
- Records mesh rules on `connectLayers(...)` and keeps tracts from `connectLayersWindowed(...)` to support deterministic auto‑wiring after growth.
- Ports as edges (scalar edge layer; InputLayer2D for images). Bind with p=1.0 fan‑out.
- Ticks: scalar `tick(...)`; 2D `tick_2d(...)` (`tick_image` delegates); ND scaffolding present.
- Metrics: delivered events, slots, synapses, optional spatial metrics, and optional growth event details.

Layer
- Mixed E/I/M population sharing a LateralBus (inhibition/modulation; increments step on decay).
- Holds per‑layer neuron limit (optional) and Region backref for auto‑wiring.
- `try_grow_neuron(seed)`: create same‑kind neuron, copy bus/config/limits, append, then ask Region to auto‑wire via recorded rules/tracts.

Neuron
- Slots: map from slot key → Weight (scalar key or packed 2D rc‑bin).
- Methods: `on_input`, `on_input_2d`, `on_output`, `fire` (subclass behavior), hooks on fire for tracts/observers.
- Focus state: FIRST anchor for scalar; 2D anchor (FIRST or ORIGIN) for spatial.
- Growth bookkeeping: `last_slot_used_fallback`, `fallback_streak`, `last_growth_tick`, `owner`.
- Frozen slot helpers: `freeze_last_slot()`, `unfreeze_last_slot()` (unfreeze sets a one‑shot reuse hint).

Weight / Synapse
- Weight keeps strength, threshold, EMA rate, first‑seen flag, frozen flag.
- Synapse stores target and an optional feedback tag. Mesh edges complement tract delivery.

---

## 3) Focus & Slotting

Temporal Focus (FIRST)
```
scale = max(|anchor|, epsilon_scale)
delta_pct = 100 * |x - anchor| / scale
slot_id  = floor(delta_pct / bin_width_pct)
```
Strict capacity
- Effective limit = `neuron.slot_limit` if set else `slot_cfg.slot_limit`.
- If under limit and slot missing → create.
- If at capacity and a new bin is desired or desired id out‑of‑domain → reuse a deterministic existing id; set `last_slot_used_fallback = True`.
- No new allocations at capacity (except bootstrap when slots are empty).

Spatial Focus (2D)
- Maintain (row,col) anchor (FIRST or ORIGIN); compute `(row_bin, col_bin)` using per‑axis bin widths and pack into a deterministic key.
- Same strict capacity and fallback semantics as scalar; mark `last_slot_used_fallback` when reusing.

---

## 4) Frozen Slots

Semantics
- Freeze: subsequent `reinforce` and `update_threshold` on that slot are no‑ops.
- Unfreeze: re‑enable learning and set a one‑shot hint to reuse the last slot once so adaptation resumes on the intended slot.

Tests
- Reinforcement does not alter a frozen slot; threshold calculations treat frozen slots as fixed; unfreeze resumes adaptation on the same slot after a single reuse.

---

## 5) Windowed Wiring (Tracts)

API
- `connect_layers_windowed(src2D, dst, kernel_h, kernel_w, stride_h, stride_w, padding, feedback=False)`.

Behavior
- VALID/SAME windows; for SAME and even kernels, center = floor(midpoint) clamped to bounds.
- Destination is OutputLayer2D: map each window’s pixels to the center output neuron; dedupe `(src,center)` edges.
- Destination is a generic Layer: subscribe each participating source pixel and let destination handle 2D context (`propagate_from_2d`).

Return value
- The number of unique source subscriptions (distinct source pixels that participate in ≥1 window), not raw (src,dst) pairs.

Growth & tracts
- When a source layer grows, the Region calls `attach_source_neuron(new_index)` on relevant tracts so new sources deliver immediately.

---

## 6) Buses, Pulses, & Two‑Phase Tick

Two‑phase tick
1. Phase A (Drive): inject input; neurons evaluate `on_input`/`on_input_2d`; hooks notify tracts/mesh; local propagation.
2. Phase B (Output/Post): outputs finalize; any per‑tick post logic runs.

Then
- Call `end_tick()` on each layer; decay each layer’s LateralBus (inhibition *= decay; modulation = 1.0; `current_step += 1`).
- Region bus (if present) may decay with the same semantics.

Pulses
- `pulse_inhibition(f)` / `pulse_modulation(f)` are one‑tick nudges applied to the upcoming tick.

---

## 7) Growth Hierarchy (Slots → Neurons → Layers → Regions)

7.1 Slot growth (in‑neuron)
- Create/select until `slot_limit`. At capacity, reuse deterministically and set `last_slot_used_fallback = True`.

7.2 Neuron growth (in‑layer)
- Track `fallback_streak` when at capacity and fallback was used; when `streak ≥ fallback_growth_threshold` and cooldown passed (via bus `current_step`), call `layer.try_grow_neuron(seed)`.
- Auto‑wiring: Region replays mesh rules (outbound and inbound) and, for windowed tracts, calls `attach_source_neuron(new_index)`.

7.3 Layer growth (Region‑mediated)
- If a layer hits a neuron limit and policy allows, Region adds a spillover layer (default excitatory‑only, size derived deterministically) and wires saturated → new. Default `wire_probability = 1.0` for deterministic topology; projects may override.

7.4 Region growth (automatic)
- At end‑of‑tick, compute pressure (avg slots per neuron and/or % of neurons at capacity using fallback). If thresholds and cooldown pass, add exactly one layer; deterministic wiring using the same RNG and recorded rules.

---

## 8) Growth Policy (Runtime Knobs)

Per‑neuron (via SlotConfig)
- `growth_enabled` (default True)
- `neuron_growth_enabled` (default True)
- `fallback_growth_threshold` (default 3)
- `neuron_growth_cooldown_ticks` (default 0 unless raised)
- `slot_limit` (default 16; −1 = unlimited)

Per‑layer
- Optional `neuron_limit` to trigger layer growth escalation when neuron growth is requested but blocked.

Per‑region (policy object / fields)
- `enable_layer_growth` (bool)
- `enable_region_growth` (bool, when distinguished)
- Triggers: `avg_slots_threshold` or `% at cap with fallback`
- Cooldowns: `layer_cooldown_ticks` (and `region_cooldown_ticks` if separate)
- Determinism: `rng_seed`
- Spillover parameters: `new_layer_excitatory_count`, `wire_probability` (default 1.0)

---

## 9) Ports as Edges

Binding an input port creates/reuses an edge layer (scalar: 1‑neuron; 2D: InputLayer2D). The Region wires edge → targets with p=1.0; outbound ports mirror this idea. This keeps Region decoupled from payload shapes while unifying ingress/egress semantics.

---

## 10) Deterministic Wiring

- Mesh rules: each `connectLayers` call records `{src, dst, prob, feedback}` for replay during growth auto‑wiring.
- Tracts: windowed connections retain a Tract; on source growth, `attach_source_neuron(new_index)` subscribes the new source.
- All random draws use the Region’s RNG for reproducibility.

---

## 11) Language Parity & Style

General
- Public names and call shapes align; if behavior changes, keep delegating aliases.
- Avoid single/double‑letter identifiers in public code; use descriptive names.

Python
- Snake_case; no leading underscores for public attributes/methods. Tests under `src/python/tests`.

C++
- Headers are canonical for shape; prefer smart pointers; `LateralBus/RegionBus.decay()` increments step.

Java
- CamelCase public API; `SlotConfig` exposes growth knobs; `Layer.tryGrowNeuron` clones seed kind and calls `Region.autowireNewNeuron`.

Mojo
- `struct` + `fn` with explicit types; snake_case naming; align semantics and step counter.

Parity matrix (high‑level expectations)
- Strict slot capacity + fallback (scalar & 2D): all languages.
- Frozen slot + one‑shot reuse after unfreeze: Python/Java/C++; Mojo must provide a one‑shot hint.
- Neuron growth via fallback streak + cooldown (bus step): all languages.
- Auto‑wiring (mesh replay + tract re‑attach): Python/C++/Java; Mojo to mirror.
- Region growth (avg or % at cap; cooldown; 1/tick; deterministic wiring): all languages.
- Bus decay: multiplicative inhibition decay; modulation reset 1.0; `current_step += 1`.

---

## 12) Metrics & Counters (per tick)

- `deliveredEvents`, `totalSlots`, `totalSynapses`.
- Optional spatial metrics: activePixels, centroidRow/Col, bbox (computed from last OutputLayer2D frame; fall back to input if output is all zeros).
- Optional growth details: `added_neurons [(layer_id, neuron_index, kind)]`, `added_layers [layer_id]` and `growth_events_this_tick`.

---

## 13) Testing & Validation

Unit/Smoke
- Temporal Focus: monotonic ramp → multiple slots; strict cap enforces no growth at limit.
- Frozen slots: frozen slot ignores reinforcement/θ updates; unfreeze prefers last slot once.
- Windowed wiring: VALID/SAME center rule; dedupe; return unique source subscriptions.
- Neuron growth: at capacity + fallback streak triggers growth; auto‑wiring matches mesh/tract expectations.
- Layer/Region growth: triggers via policy; cooldown respected; one growth per tick; deterministic wiring.

Determinism
- With fixed seeds, wiring topologies and growth event sequences repeat across runs.

---

## 14) Backward Compatibility & Versioning

Backward compatibility
- `tick_image` remains and delegates to `tick_2d`.
- Demos and prune stubs may continue to compile/run without changes.

Versioning
- This document is V5 (supersedes V4). Keep Contract v5 YAML in sync (ports, growth knobs, windowed wiring semantics).

---

## 15) Security & Safety

- Growth actions are best‑effort; never throw into `Region.tick()`; guard and continue.
- Prevent unbounded growth by default with slot limits, per‑layer neuron caps, max layers, and cooldowns.
- Windowed wiring dedupes to avoid unintended fan‑out explosions.

---

## 16) Quick Examples

Python (enable growth on hidden layer with windowed wiring)
```python
from region import Region

r = Region("demo")
lin = r.add_input_layer_2d(8, 8, gain=1.0, epsilon_fire=0.01)
lh  = r.add_layer(excitatory_count=4, inhibitory_count=0, modulatory_count=0)
r.connect_layers_windowed(lin, lh, 2, 2, 2, 2, "valid")
r.bind_input("img", [lin])

for n in r.get_layers()[lh].get_neurons():
    n.slot_cfg.growth_enabled = True
    n.slot_cfg.neuron_growth_enabled = True
    n.slot_cfg.fallback_growth_threshold = 2
    n.slot_limit = 2

for frame in frames:
    r.tick_2d("img", frame)
```

C++ (deterministic spillover outline)
```cpp
Region region("demo");
int lin = region.addInputLayer2D(8, 8, 1.0, 0.01);
int lh  = region.addLayer(4, 0, 0);
region.connectLayersWindowed(lin, lh, 2, 2, 2, 2, "valid");
// Configure policy: avg_slots_threshold or % at cap, cooldown, wire p=1.0
// End-of-tick: region may add a spillover layer and wire deterministically.
```

---

### Appendix — Suggested Defaults

| Knob | Default | Notes |
|---|---:|---|
| slot_limit | 16 | per‑neuron; −1 = unlimited |
| bin_width_pct | 10.0 | scalar focus |
| row/col_bin_width_pct | 10.0 | 2D focus |
| growth_enabled | True | per‑neuron |
| neuron_growth_enabled | True | per‑neuron |
| fallback_growth_threshold | 3 | consecutive uses |
| neuron_growth_cooldown_ticks | 0 | raise for production |
| region avg_slots_threshold | 12.0 | with limit 16 |
| region % at‑cap threshold | 50% | complement to avg |
| layer_cooldown_ticks | 20 | controls pace |
| spillover wire_probability | 1.0 | deterministic |
