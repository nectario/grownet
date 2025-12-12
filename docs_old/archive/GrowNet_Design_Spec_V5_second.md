# GrowNet Design Specification — V5

**Status:** Candidate for merge
 **Date:** 2025‑09‑04
 **Scope:** Core data plane (Region/Layer/Neuron/Slot), Temporal & Spatial (2D) Focus, *automatic growth* (slots→neurons→layers→regions), tract/windowed wiring, two‑phase ticking, multi‑language parity (Python = C++ = Java = Mojo).

> **What changed since V4:** V5 turns the earlier “growth hooks” into a concrete, deterministic growth system with strict slot capacity, fallback detection, frozen‑slot semantics, and end‑of‑tick region growth. Wording and APIs remain compatible with V4 where possible; where behavior differs, we keep aliases and document the deltas. 

------

## 1) Goals & Non‑Goals

**Goals**

- Deterministic learning primitives that *grow capacity*: first within a neuron (slots), then within a layer (neurons), then within a region (layers), and finally across regions (optional).
- Consistent behavior across Python, C++, Java, and Mojo (naming and typing idiomatic to each language).
- Clear two‑phase ticks with per‑tick bus decay and a monotonic **step counter** used for cool‑downs and metrics.
- Windowed (tract) wiring for 2D paths with deterministic center mapping and automatic re‑attachment after growth.
- *Clarity over cleverness:* predictable wiring, no hidden global state, and explicit policies for growth & decay.

**Non‑Goals (this release)**

- Advanced learning rules (Hebbian variants, STDP, rich modulatory chemistry).
- Distributed or multi‑region runtime orchestration.
- Full ND focus operations (we expose ND layer shapes; ND ticking is staged next).

------

## 2) Core Model

### 2.1 Region

A `Region` owns:

- A list of `Layer` objects.
- Wiring helpers:
  - `connect_layers(source, dest, probability, feedback=False)` (mesh)
  - `connect_layers_windowed(source_2d, dest, kernel_h, kernel_w, stride_h, stride_w, padding, feedback=False)` (tract)
- Port binding:
  - `bind_input(name, [layers])`, `bind_input_2d(name, h, w, gain, eps_fire, [layers])`
  - `bind_output(name, [layers])`
- Tick orchestration:
  - Scalar: `tick(port, value)`
  - 2D: `tick_2d(port, frame)` (aliases like `tick_image` remain)
- Maintenance: `prune(...)` (safe no‑op stub until pruning is finalized).
- **Growth policy & engine** (Section 5): computes pressure at end‑of‑tick and, if warranted, grows **one** new layer deterministically.

> **Determinism:** all stochastic decisions (mesh and spillover wiring) use a Region‑scoped RNG seeded once per Region.

### 2.2 Layer

A mixed population (E/I/M). Responsibilities:

- Construct E/I/M neurons with a default `SlotConfig`.
- Hold a `LateralBus` (shared by neurons) with **current_step** incremented each tick.
- Provide `try_grow_neuron(seed_neuron)` which:
  1. Instantiates a neuron of the *same kind* as `seed_neuron`.
  2. Copies bus binding, slot policy, and slot limit.
  3. Appends to the layer and asks the Region to **auto‑wire** it according to stored mesh rules and any windowed tracts.

### 2.3 Neuron

A neuron has:

- Slot memory: `slot_id -> Weight` (scalar) or `(row_bin,col_bin) -> Weight` (2D encoded key).
- Threshold & firing logic (`on_input`, `on_input_2d`, `on_output`).
- Firing hooks to notify Tracts and mesh edges.
- *Focus state* (Temporal: FIRST anchor; Spatial: 2D row/col bins).
- **Growth bookkeeping**:
  - `last_slot_used_fallback: bool`
  - `fallback_streak: int`
  - `last_growth_tick: int`
  - `owner: Layer` (set on creation)
- **Frozen slot** controls:
  - `freeze_last_slot()`, `unfreeze_last_slot()`
     Unfreeze sets a *one‑shot hint* (“prefer last slot once”) so learning resumes on the intended slot.

### 2.4 Weight / Slot / Synapse

- `Weight` represents the per‑slot compartment (value + threshold + frozen flag).
- `Synapse` is a directed connection `source -> target` with an optional `feedback` tag (for back/winner‑take‑all style loops).
- “Slot” is a conceptual view: a `Weight` stored under a specific bin key.

------

## 3) Focus & Slotting

### 3.1 Temporal Focus (Scalar)

**Anchor‑first binning** (FIRST mode):

```
scale = max(|anchor|, epsilon_scale)
delta_pct = 100 * |x - anchor| / scale
slot_id = floor(delta_pct / bin_width_pct)
```

**Strict capacity:**
 Let `effective_limit = neuron.slot_limit if set else slot_cfg.slot_limit`.

- If `slot_count < effective_limit` and slot_id not present → **create** slot.
- If at capacity and a **new** bin would be selected → **reuse fallback** deterministically (e.g., `slot_id = effective_limit-1` or reuse first existing id); **never create** a new slot at capacity (except bootstrap when there are none).
- Set `neuron.last_slot_used_fallback = True` whenever capacity forces reuse or the desired id is out‑of‑domain.

### 3.2 Spatial Focus (2D)

- Maintain an (r,c) *anchor* the first time spatial is used on a neuron.
- Compute `(row_bin, col_bin)` with per‑axis bin widths.
- Keys are packed deterministically (e.g., `row_bin * K + col_bin` with a large `K`).
- **Strict capacity** mirrors scalar rules:
  - Create if under capacity; otherwise reuse a deterministic fallback (e.g., `(L-1,L-1)` or first existing key).
  - Set `last_slot_used_fallback` when capacity forces reuse.

### 3.3 Frozen Slots

- `freeze_last_slot()` sets the current slot’s frozen bit; frozen slots do not adapt during inhibition/modulation updates.
- `unfreeze_last_slot()` clears the bit and sets a **one‑shot preference** so the very next selection reuses that slot (helps “resume adaptation” precisely).

------

## 4) Windowed (Tract) Wiring for 2D

`connect_layers_windowed` builds *deterministic* subscriptions:

- For `dest = OutputLayer2D`: each source pixel connects to the *window center* neuron of the window that covers it. If multiple windows include the pixel, dedupe `(src_idx, center_idx)`.
- For other destinations: the first time a source pixel participates, connect it to **all** destination neurons (deterministic fan‑out).
- The call returns the count of **unique source pixels** that were subscribed.
- The Region stores the created **Tract** so that when a layer **grows** (adds a source neuron), the tract can **attach** the new source to the same downstream path.

------

## 5) Automatic Growth

**Golden Rule:** Grow strictly “upward”, in this order: **slots → neurons → layers → regions**. Never skip levels.

### 5.1 Slot Growth (in‑neuron)

- A neuron accumulates slots until `effective_limit`.
- When a desired new bin cannot be created (limit hit), selection **reuses fallback** and flips `last_slot_used_fallback = True`.

### 5.2 Neuron Growth (in‑layer)

A neuron requests growth from its `owner` when all are true:

- **At capacity**: `len(slots) >= effective_limit`.
- **Pressure**: `last_slot_used_fallback == True`.
- **Streak**: this condition holds for `fallback_growth_threshold` consecutive events.
- **Cooldown**: `(current_step - last_growth_tick) >= neuron_growth_cooldown_ticks`.

If granted, the layer calls `try_grow_neuron(seed)`:

- Create a neuron of the **same kind** (E/I/M) as `seed`.
- Copy bus binding, slot policy, and slot limit.
- Append to the layer and **auto‑wire** via Region rules:
  - **Mesh**: replay outbound and inbound rules with original probabilities (Bernoulli).
  - **Tracts**: if the growing layer is a **source**, call `tract.attach_source_neuron(new_index)`.

### 5.3 Layer (Region) Growth

At **end‑of‑tick**, the Region evaluates policy:

- **Triggers (OR):**
  - `average_slots_per_neuron >= avg_slots_threshold`, or
  - `% of neurons at capacity AND using fallback >= percent_at_cap_threshold`.
- **Cooldown:** `(current_step - last_region_growth_step) >= layer_cooldown_ticks`.
- **One per tick:** grow at most one new layer per Region tick.
- **Selection:** choose the **most saturated** layer (highest pressure) as the *saturated layer*.

**Action (deterministic):**

1. Create a *spillover* layer (by default excitatory‑only with a small count; tunable).
2. **Wire saturated → new with probability = 1.0** (doc‑standard default for clarity).
    Optionally duplicate inbound mesh rules as warranted by your experiment.
3. Record the event in Region metrics/logs.

------

## 6) Buses, Pulses, & Ticking

**Two‑phase tick (per Region):**

1. **Phase A – Drive:** inputs propagate through layers; neurons may fire; hooks notify tracts/mesh.
2. **Phase B – Output/Post:** output neurons emit, any per‑tick post logic runs.

**Then:**

- Call `end_tick()` on each layer (neurons may do housekeeping).
- **Decay** each layer’s `LateralBus`:
  - Multiply inhibition by decay factor (toward baseline),
  - Reset modulation to **1.0**,
  - Increment `current_step += 1`.
     The **step counter** is the canonical clock for cooldowns.

`pulse_inhibition(f)` and `pulse_modulation(f)` are **one‑tick** nudges (applied to the upcoming tick only).

------

## 7) Policies & Defaults

### 7.1 SlotConfig (per neuron, via layer defaults)

- `anchor_mode = FIRST`
- `bin_width_pct = 10.0`
- `epsilon_scale = 1e-6`
- `slot_limit = 16` (per‑neuron; `-1` = unlimited)
- **Growth knobs:**
  - `growth_enabled = True`
  - `neuron_growth_enabled = True`
  - `fallback_growth_threshold = 3`
  - `neuron_growth_cooldown_ticks = 0` (lab‑friendly; raise for production)
  - `layer_growth_enabled = False` (neurons may request escalation, but Region policy governs actual layer growth)

### 7.2 Region Growth Policy (per region)

- `enable_layer_growth = True/False`
- `avg_slots_threshold` (e.g., 12.0 with `slot_limit = 16`)
- `percent_at_cap_threshold` (e.g., 50%)
- `layer_cooldown_ticks` (e.g., 20)
- `max_layers` (optional cap)
- `rng_seed` (defaults to 1234)
- `spillover_size` (e.g., 4 excitatory)
- `spillover_wire_probability = 1.0` (default for determinism)

------

## 8) Deterministic Wiring

- **Mesh rules:** whenever `connect_layers` is called, the Region records `{src, dst, prob, feedback}`. Growth replays these rules to auto‑wire newly added neurons/layers.
- **Tracts:** windowed connections retain a `Tract` object; when a source layer grows, `attach_source_neuron(new_index)` wires the new source to downstream exactly like its peers.
- All random draws use the Region RNG for reproducibility.

------

## 9) Language Parity & Style

**General principles**

- Public names are stable; if behavior changes, keep a delegating alias.
- Avoid single‑letter / double‑letter variable names in public code.
- Python: snake_case, **no leading underscores** for public attributes or functions.
- Mojo: `struct` instead of `class`; `fn` with explicit types; **no leading underscores** for public identifiers.
- C++: headers describe the canonical shape; prefer `std::shared_ptr`/`std::unique_ptr`; avoid over‑templating.
- Java: remains a first‑class reference for API shape.

**Parity matrix (high level)**

- **Strict slot capacity + fallback marking:** **All** languages (scalar & 2D).
- **Frozen‑slot + one‑shot reuse after unfreeze:** Python/Java **yes**; C++ **yes**; Mojo **required** by spec (ensure “prefer once” hint exists).
- **Neuron growth (streak + cooldown via bus step):** All languages.
- **Auto‑wiring new neurons (mesh + tract re‑attach):** Python/C++/Java **yes**; Mojo **must** mirror.
- **Region growth policy (avg or % at cap; cooldown; 1/tick; deterministic wiring):** All languages.
- **Bus decay semantics & step counter:** All languages (multiply inhibition decay; reset modulation=1.0; `current_step += 1`).

------

## 10) Metrics & Counters

Per Region (updated at end‑of‑tick):

- `current_step`
- `num_layers`, `num_neurons`, `num_synapses`
- `num_slots_total` (sum across neurons)
- `growth_events_this_tick` with details:
  - `added_neurons: [(layer_id, neuron_index, kind)]`
  - `added_layers: [layer_id]`

These are *observability aids*, not programmatic guarantees.

------

## 11) Backward Compatibility

- `tick_image(...)` remains as an alias to `tick_2d(...)`.
- Existing demos using mesh wiring or basic 2D wiring continue to run.
- `prune(...)` can return a neutral summary until pruning lands; demos may keep their `prune` lines.

------

## 12) Security & Safety

- All growth actions are **best‑effort** and **must not throw** into `Region.tick(...)`. Guard, log, and continue.
- Prevent unbounded growth by default via `slot_limit`, per‑layer caps (optional), and Region `max_layers` / cooldowns.
- Windowed wiring dedupes `(src,center)` to avoid accidental fan‑out explosions.

------

## 13) Quick Examples

### 13.1 Enable growth (Python)

```python
from region import Region
r = Region("demo")
lin = r.add_input_layer_2d(8, 8, gain=1.0, epsilon_fire=0.01)
lh = r.add_layer(excitatory_count=4, inhibitory_count=0, modulatory_count=0)
r.connect_layers_windowed(lin, lh, 2, 2, 2, 2, "valid")
r.bind_input("img", [lin])

# Tune growth on hidden neurons
for n in r.get_layers()[lh].get_neurons():
    n.slot_cfg.growth_enabled = True
    n.slot_cfg.neuron_growth_enabled = True
    n.slot_cfg.fallback_growth_threshold = 2
    n.slot_limit = 2

# Drive a few frames; growth triggers automatically
for frame in frames:
    r.tick_2d("img", frame)
```

### 13.2 Deterministic spillover (C++ outline)

```cpp
Region region("demo");
int lin = region.addInputLayer2D(8, 8, 1.0, 0.01);
int lh  = region.addLayer(4, 0, 0);
region.connectLayersWindowed(lin, lh, 2, 2, 2, 2, "valid");
// Region growth policy: avg_slots_threshold, percent_at_cap_threshold, cooldown, p=1.0 wiring
// ... feed frames; at end-of-tick, region may grow a spillover layer, then auto-wire deterministic edges
```

------

## 14) Validation Checklist

- **A. Slot growth**
  - Strict capacity (no new slots beyond limit except bootstrap).
  - Fallback flag is set when capacity forces reuse or id out‑of‑domain.
  - Scalar and 2D parity.
  - Frozen/unfreeze with *one‑shot reuse*.
- **B. Neuron growth**
  - Fallback streak with cooldown via bus step.
  - Owner backref present on all neurons (including I/O for parity).
  - Clone same kind; copy cfg and limits.
  - Auto‑wire (mesh rules; tract re‑attach for sources).
- **C. Region (layer) growth**
  - Triggers: avg‑slots OR % at‑cap‑using‑fallback; cooldown; **one per tick**.
  - Deterministic RNG; **p=1.0** spillover wiring by default.
- **D. Bus & tick**
  - Two‑phase tick → layer end_tick → bus decay.
  - `current_step` increments exactly once per tick.
- **E. Docs & tests**
  - Growth smoke tests and windowed wiring tests exist per language.
  - Demos continue to compile; `prune(...)` is a safe stub.

------

## 15) Versioning

- **This document:** **V5** (supersedes V4). 
- Contracts: update `contracts/GrowNet_Contract_v5.yaml` in lock‑step (ports, ticks, growth knobs).
- Source headers and public names must carry minimal deltas; if behavior changes, keep delegating aliases.

------

### Appendix A — Defaults (suggested)

| Knob                           | Default | Notes                      |
| ------------------------------ | ------- | -------------------------- |
| `slot_limit`                   | 16      | per‑neuron; `-1` unlimited |
| `bin_width_pct`                | 10.0    | scalar focus               |
| `row/col_bin_width_pct`        | 10.0    | 2D focus                   |
| `growth_enabled`               | True    | per neuron                 |
| `neuron_growth_enabled`        | True    | per neuron                 |
| `fallback_growth_threshold`    | 3       | consecutive                |
| `neuron_growth_cooldown_ticks` | 0       | for experimentation        |
| Region `avg_slots_threshold`   | 12.0    | with limit 16              |
| Region `% at cap threshold`    | 50%     | or as needed               |
| Region `layer_cooldown_ticks`  | 20      | controls pace              |
| Spillover `wire_probability`   | **1.0** | deterministic              |

------

If you want, I can also generate a short **“What’s new in V5 vs V4”** changelog and an updated **Contract v5** YAML to keep everything aligned with this spec.
