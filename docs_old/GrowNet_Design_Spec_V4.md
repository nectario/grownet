# GrowNet Design Specification — V4
**Status:** Draft for review  
**Date:** 2025-08-30  
**Scope:** Core data plane (Region/Layer/Neuron/Slot), Focus (Temporal), early hooks for Growth, multi‑language parity (Java=C++=Python=Mojo).

> This V4 consolidates the *Temporal Focus* design (anchor-based slotting), ports-as-edges model, 2D input path, and early *Growth* hooks. It replaces V3 while preserving names/calls used by demos. Spatial Focus is outlined but left for Phase B.

---

## 1. Goals & Non‑Goals
**Goals**
- Deterministic, minimal core primitives that match across Java, C++, Python, Mojo.
- Temporal Focus: anchor‑based slot selection that avoids “drift to last input” and enables outlier detection.
- Growth hooks: non-intrusive entry points for neuron/layer growth decisions.
- Shape‑aware inputs (2D today; ND wiring in place) with ports modeled as edge layers.
- Safety and clarity: no silent removal of public methods; delegating aliases when behavior changes.

**Non‑Goals (V4)**
- Full Spatial Focus implementation (Phase B).
- Full Market/Registry features.
- Any heavy learning rule beyond current threshold/weight stubs.
- Distributed execution.

---

## 2. Core Model
### 2.1 Region
A `Region` groups `Layer`s, owns simple wiring helpers, and orchestrates `tick(...)` and `prune(...)`.

Key responsibilities:
- **Layer management:** `addLayer(e, i, m)`, `getLayers()`.
- **Ports as edges:** `bindInput(port, layers)`, `bindInput2D(port, h, w, gain, epsFire)`, and `bindOutput(port, layers)` create or reuse small edge layers which then connect with p=1.0.
- **Tick:** 
  - Scalar: `tick(port, value)`
  - 2D: `tick2D(port, double[][] frame)`; `tickImage(...)` delegates to `tick2D(...)`.
  - (ND path exists in types/wiring; Phase B to finalize `tickND`). 
- **Pulses:** `pulseInhibition(f)`, `pulseModulation(f)` touch region/layer lateral buses for the next tick only.
- **Maintenance:** `prune(staleWindow, minStrength)` delegates to neurons.

**Metrics**: region aggregates simple counts (synapses, slots, delivered events) for visibility, not as guarantees.

### 2.2 Layer
A mixed population. Constructor defines neuron counts (excitatory/inhibitory/modulatory) and a default `SlotConfig`. Layers expose their `LateralBus` and the neuron list.

### 2.3 Neuron
Holds:
- Outgoing synapses (to other neurons)
- Slot map `slot_id → Weight`
- Last‑input bookkeeping (for legacy deltas)
- **Temporal Focus state (new):**
  - `focusAnchor: double`
  - `focusSet: boolean`
  - `focusLockUntilTick: long` (reserved for attention/pulsing locks)
- Fire path updates the selected slot and applies threshold/gain; hooks can observe fires.

### 2.4 Slot, Synapse, Weight
- `Slot` is represented by a `Weight` compartment keyed by bin.
- `Synapse` wraps a `Weight` with source/target and optional `feedback` flag.

---

## 3. Temporal Focus (V4)
**Problem:** With incremental inputs (e.g., 1.0→1.1→1.2…), last‑value deltas funnel most samples into one slot.

**Approach:** **Anchor‑first binning** — establish a focus anchor (FIRST mode). Map each new input `x` to a percent delta relative to the anchor:
```
scale = max(|anchor|, epsilon_scale)
delta_pct = 100 * |x - anchor| / scale
slot_id = floor(delta_pct / bin_width_pct)
```
Ensure capacity by creating the slot if under `slot_limit`, else clamp to `[0, slot_limit-1]`.

**Config (cross‑language, exposed via SlotConfig):**
- `anchor_mode`: `FIRST` (V4), stubs for `EMA`, `WINDOW`, `LAST`.
- `bin_width_pct`: default 10.0.
- `epsilon_scale`: default 1e-6 (avoids divide‑by‑zero as anchor→0).
- `recenter_threshold_pct`, `recenter_lock_ticks`, `anchor_beta`: reserved for EMA/WINDOW.
- `outlier_growth_threshold_pct`: threshold for neuron growth hook.
- `slot_limit`: default 16 (per‑neuron functional capacity).

**Integration points:**
- Java: methods exist in `SlotEngine` to compute slot and ensure capacity; Neuron carries focus state.
- Python/Mojo/C++ mirror the same logic with idiomatic names and typing.
- Callers can still use legacy `slotId(last, current)` paths; anchor logic is the default for Focus flows.

---

## 4. Growth (V4 hooks)
**Goal:** Spawn capacity when (a) neuron is saturated (`len(slots) ≥ slot_limit`) **and** (b) input is an outlier vs anchor (`delta_pct ≥ outlier_growth_threshold_pct`).

**Policy/Engine:**
- `GrowthPolicy`: runtime tunables and cooldowns; safe defaults.
- `GrowthEngine.maybeGrowNeurons(region, policy)`: best‑effort hook after region metrics are computed; never throws.
- Layer growth pressure: simple proxy on “avg slots per neuron” can create a new layer and lightly connect it forward.

**Safety:** Reflection / guards ensure Growth hooks do not compile‑break older Layer APIs; placeholders are no‑ops.

---

## 5. Ports as Edges
Binding an input/output port lazily creates a 1‑neuron edge layer which is then connected with probability 1.0 to target layers. For 2D inputs, `InputLayer2D` is created and wired as the edge. This keeps **Region** decoupled from payload shapes while giving consistent wiring semantics.

---

## 6. 2D & ND Inputs
- **2D:** `addInputLayer2D(h, w, gain, epsFire)`, `bindInput2D(port, ... targets ...)`, `tick2D(port, frame)`.
- **ND:** `InputLayerND` and `bindInputND(...)` exist; `tickND` is planned for Phase B (no caller breakages).

---

## 7. Lateral Bus & Pulses
`LateralBus` supports transient modulation/inhibition that decay each tick. Region exposes convenience pulses that also set/decay each layer’s bus, making pulses ephemeral by design.

---

## 8. Language Parity (authoritative: Java)
- **Java** is the gold standard for names/semantics.
- **C++** mirrors structure (headers are canonical for shapes); prefer `unique_ptr/shared_ptr` where applicable.
- **Python** uses snake_case and no leading underscores for fields.
- **Mojo** uses `struct`, `fn`, and fully typed parameters; avoid clever tricks; keep code Python‑like.

**Public methods are never removed**. When behavior changes, keep a delegating alias (e.g., `tickImage → tick2D`).

---

## 9. Testing & Examples
- Minimal smoke tests: scalar tick produces slots along a simple sequence; 2D tick forwards a frame through the input edge.
- Temporal Focus tests: assert slot count grows across a monotonic ramp given default bin width.
- Growth smoke: when a neuron at capacity receives outlier input, GrowthEngine is invoked (no hard assertion on spawn in V4).

---

## 10. Backward Compatibility & Migration
- Code that called legacy percent‑delta (last→current) still runs; Focus flows swap to anchor‑based logic.
- `tickImage` remains and delegates to `tick2D`.
- Port binding API is stable; ND binding exists and becomes first‑class in Phase B.

---

## 11. Open Items (Phase B and beyond)
- **Spatial Focus**: top‑k salient cells/patches over 2D/ND tensors with attention windows that track moving salient regions.
- **Anchor modes**: EMA and WINDOW semantics + re‑centering policy.
- **Richer growth**: better pressure metrics, wiring inheritance policies, and tract‑level pruning.
- **Contract v4**: align the protocol YAML to this spec (ports, tick2D/ND, Focus/Growth knobs).
- **Docs**: update Field Guide, Glossary, Quick Start, and Style/Parity to reflect Focus/Growth.

---

## 12. Reference (selected signatures)
> Exact names vary slightly per language; Java shown.

```java
// Region
int addLayer(int excitatory, int inhibitory, int modulatory);
int addInputLayer2D(int height, int width, double gain, double epsilonFire);
void bindInput(String port, List<Integer> layers);
void bindInput2D(String port, int h, int w, double gain, double epsFire, List<Integer> layers);
RegionMetrics tick(String port, double value);
RegionMetrics tick2D(String port, double[][] frame);
RegionMetrics tickImage(String port, double[][] frame); // delegates to tick2D
Region.PruneSummary prune(long synapseStaleWindow, double synapseMinStrength);

// Neuron (selected)
double getFocusAnchor(); // V4
Map<Integer, Weight> getSlots();

// SlotEngine (selected)
int selectOrCreateSlot(Neuron n, double x, SlotConfig cfg); // anchor‑based FIRST mode
```

---

## 13. Security & Safety
- Growth hooks must never throw into `Region.tick()`; guard and log only.
- Avoid unbounded growth by default (`slot_limit`, cooldowns, maxLayers).

---

## 14. Versioning
- **This document:** V4 (supersedes V3).
- Contracts: bump to `contracts/GrowNet_Contract_v4_master.yaml` once updated.
- Source doc headers should carry `// [GROWNET:ANCHOR::<name>]` markers for safe Codex patches.
