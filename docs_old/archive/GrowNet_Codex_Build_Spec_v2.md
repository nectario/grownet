# GrowNet — Codex Build Spec (v2)

**Purpose:** A precise, code‑generation‑friendly specification for producing **consistent** GrowNet implementations in **Python 3.14**, **Java 17+ (Maven)**, **C++17 (CLion/CMake)**, and **Mojo**.  
**Audience:** Code generation systems (e.g., Codex) and maintainers.  
**Lineage:** This spec supersedes v1 and aligns with the unified `onInput / onOutput` architecture; it builds on the original **“GrowNet: Theory of Change”** document. fileciteturn6file0

---

## 0. Design Rules (non‑negotiable)

1) **Unified neuron contract** (all neuron types in every language):
   - `onInput(value, …) -> fired: bool`
   - `onOutput(amplitude) -> None` (called **only if** `fired` is true).
2) **Actuator boundary:** **Output neurons never propagate** (they must **not** call `fire`). They **accumulate** and are finalized at layer level.
3) **Layer firing path:** When a neuron fires, the layer must **first** call `neuron.onOutput(value)` and **then** perform any propagation.  
4) **Single‑slot IO neurons:** **InputNeuron** and **OutputNeuron** each own **slot 0** only; hidden neurons can have multiple slots.
5) **Buses not backprop:** No global error signals. Learning is **local**; layers have a **LateralBus** with inhibition & modulation that **decay** to neutral each tick.
6) **Naming & style:**
   - Prefer **descriptive names**; avoid cryptic initials (e.g., use `adaptSpeed` not `eta`; exception: `np`, `pd`).
   - **No leading underscores** for variables or functions.
   - **No Unicode symbols** in identifiers (e.g., do not use `β`/`η`/`Δ` in code). Use words instead.
7) **Mojo specifics:** prefer Python‑like syntax; use `fn` for functions, `alias` for constants; avoid advanced ownership keywords and exotic syntax in this version.

---

## 1. Core Data Types

### 1.1 Weight (Slot)
A per‑slot gate storing strength and adaptive threshold state.

**Fields (all languages)**
- `strengthValue: float` — synaptic efficacy; bounded, updated by `reinforce`.
- `thresholdValue: float` — adaptive θ.
- `emaRate: float` — EMA of recent spikes for homeostasis.
- `firstSeen: bool` — whether T0 imprint was applied.
- `hitCount: int` — saturates at `slotHitSaturation` (default **10_000**).

**Methods**
- `reinforce(modulationFactor: float, inhibitionFactor: float) -> None` — bounded, non‑linear update to `strengthValue`; increments `hitCount` up to saturation.
- `updateThreshold(inputValue: float) -> bool` — returns `fired`; applies **T0** imprint on first exposure and **T2** homeostasis thereafter.

**Default constants**
- `beta = 0.01` (EMA horizon), `adaptSpeed = 0.02` (threshold adapt), `targetRate = 0.05`, `epsilonFire = 0.01`, `t0Slack = 0.02`, `slotHitSaturation = 10000`.

### 1.2 Neuron (base)
**Fields**
- `slots: Map[int, Weight]` (slot id → weight).
- `firedLast: bool`, `lastInputValue: float`.
- `bus: LateralBus` (layer‑scoped view).

**Methods**
- `onInput(value, …) -> bool` — gate via slots; update local state.
- `onOutput(amplitude) -> None` — **default no‑op** (hidden & input); **accumulate** for outputs.
- `fire(amplitude) -> None` — internal relay notification; **must never be called by outputs**.

### 1.3 Neuron phenotypes
- **ExcitatoryNeuron** — default relay; inherits base behavior.
- **InhibitoryNeuron** — on spike, emits **inhibition** via the layer bus (e.g., set `inhibitionFactor < 1` for N ticks).
- **ModulatoryNeuron** — on spike, emits **modulation** via the layer bus (e.g., set `modulationFactor > 1` temporarily).
- **InputNeuron** — single‑slot sensor; **T0 imprint**; may call `fire` so routing works.
- **OutputNeuron** — single‑slot actuator; `onInput` gates only; `onOutput` accumulates; finalized via EMA; **never fires**.

### 1.4 LateralBus
```text
inhibitionFactor: float   # <= 1.0, decays to 1.0
modulationFactor: float   # >= 0.0, decays to 1.0 (neutral)
decay() -> None           # called each Region tick
```

### 1.5 Layer
- Holds `neurons`, `adjacency` (intra‑layer synapse list), and `bus`.
- **Firing path (must implement):**
  ```text
  fired = neuron.onInput(value, …)
  if fired:
      neuron.onOutput(value)            # unified hook
      propagate_from(index, value)      # intra-layer routing (hidden layers)
  ```

### 1.6 Region
- Holds `layers`, inter‑layer **tracts**, and input port bindings.
- **Convenience factories** (must exist in each language):
  - `add_input_layer_2d(height, width, gain=1.0, epsilonFire=0.01) -> int`
  - `add_layer(excitatoryCount, inhibitoryCount, modulatoryCount) -> int`
  - `add_output_layer_2d(height, width, smoothing=0.2) -> int`
- `bind_input(port: string, layerIndexes: list[int])`
- `connect_layers(srcIndex, dstIndex, probability: float, feedback: bool)`
- `tick_image(port, image[h][w]) -> metrics{{ delivered_events, total_slots, total_synapses }}`  
  (Phase A inject, Phase B flush, finalize outputs, decay buses).

---

## 2. Algorithms (language‑agnostic pseudo)

### 2.1 Non‑linear reinforcement (bounded)
```
def reinforce(weight, modulation, inhibition):
    # step scales with modulation and inhibition
    step = baseStep * modulation * inhibition
    if weight.hitCount < slotHitSaturation:
        weight.strengthValue = smoothBound(weight.strengthValue + step)  # clamp to [0, 1] or [-1, 1]
        weight.hitCount += 1
```

### 2.2 Adaptive threshold (T0 + T2 hybrid)
```
if not weight.firstSeen:
    weight.thresholdValue = effective * (1.0 - epsilonFire)   # T0 imprint
    weight.firstSeen = True

fired = (effective > weight.thresholdValue)

weight.emaRate = (1.0 - beta) * weight.emaRate + beta * (1.0 if fired else 0.0)
weight.thresholdValue += adaptSpeed * (weight.emaRate - targetRate)
return fired
```

### 2.3 Two‑phase tick
```
Phase A: For each input port:
    drive all bound input layers (e.g., forward_image)
    per layer: for each active neuron
        fired = onInput(value, bus.modulationFactor, bus.inhibitionFactor)
        if fired: onOutput(value) and propagate_intra_layer(...)

Phase B:
    flush inter-layer tracts once

Finalize:
    for each OutputLayer2D: end_tick() to update frame via EMA
    for each Layer and Region: bus.decay()
```

**Invariant:** Output neurons never call `fire`.

---

## 3. I/O for Images

### 3.1 InputLayer2D
- Shape: `height × width`; constructs `height*width` **InputNeuron** instances.
- `forward_image(image)`: for each pixel → `onInput`; if fired → `onOutput` (no‑op).

### 3.2 OutputLayer2D
- Shape: `height × width`; constructs `height*width` **OutputNeuron** instances.
- `propagate_from(sourceIndex, value)`: invoke `onInput`; if fired → `onOutput` to accumulate.
- `end_tick()`: per‑neuron EMA → frame matrix (`frame[y][x]`), reset accumulators.

---

## 4. Module Layout & Language Bindings

### 4.1 Python 3.14 (reference)
**Files (suggested):**
```
src/python/
  weight.py
  neuron.py
  excitatory_neuron.py
  inhibitory_neuron.py
  modulatory_neuron.py
  input_neuron.py
  output_neuron.py
  layer.py
  input_layer_2d.py
  output_layer_2d.py
  region.py
  image_io_demo.py
```
**Style:** descriptive names; allow `np`, `pd`; docstrings on classes/methods; typing hints where natural.

### 4.2 Java 17+
**Package:** `ai.nektron.grownet`  
**Files:**
```
InputNeuron.java, OutputNeuron.java, ExcitatoryNeuron.java, InhibitoryNeuron.java, ModulatoryNeuron.java,
Neuron.java, Weight.java, Layer.java, InputLayer2D.java, OutputLayer2D.java, Region.java, ImageIODemo.java
```
**Notes:** Maven project; `Region` exposes `addInputLayer2D`, `addLayer`, `addOutputLayer2D`, `tickImage`, `getLayers`.

### 4.3 C++17
**Headers / sources:**
```
InputNeuron.h, OutputNeuron.h, ExcitatoryNeuron.h, InhibitoryNeuron.h, ModulatoryNeuron.h,
Neuron.h, Weight.h, Layer.h, InputLayer2D.h, OutputLayer2D.h, Region.h/.cpp, ImageIODemo.cpp
```
**Notes:** Prefer readability over template wizardry; `virtual onInput/onOutput`; use `std::shared_ptr` where needed; ship a simple CMake target.

### 4.4 Mojo
**Files:**
```
weight.mojo, neuron.mojo, excitatory_neuron.mojo, inhibitory_neuron.mojo, modulatory_neuron.mojo,
input_neuron.mojo, output_neuron.mojo, layer.mojo, input_layer_2d.mojo, output_layer_2d.mojo,
region.mojo, image_io_demo.mojo
```
**Notes:** Use Python‑like syntax; `fn` for functions; `alias` for constants; avoid advanced ownership keywords for now.

---

## 5. Invariants & Validation

- **I1** Output neurons **never** call `fire`.
- **I2** Layers **always** call `onOutput(value)` when `fired` is true.
- **I3** Input/Output neurons are **single‑slot** only (slot id = 0).
- **I4** `tick_image` must finalize output frames each tick (`end_tick()`/`endTick()`).
- **I5** Buses are decayed each tick; factors trend to `1.0` (neutral).

**Recommended unit tests (per language)**
1) **T0 imprint:** First stimulus sets θ below effective value; second same stimulus fires again.
2) **T2 homeostasis:** Under repeated firing, θ increases and `emaRate` approaches `targetRate` within ±0.02 after N=1000 steps.
3) **Reinforcement bounds:** `strengthValue` remains within [0,1] (or chosen bounds) and saturates as `hitCount → slotHitSaturation`.
4) **Layer firing path:** When a neuron fires, `onOutput` is invoked exactly once before propagation.
5) **Output finalization:** After `end_tick`, per‑pixel `outputValue` equals EMA of contributions.
6) **tick_image metrics:** Returns non‑decreasing `total_slots` and coherent `delivered_events` (> 0 when activity occurs).
7) **Actuator boundary:** Outputs never create new events in tracts/intra‑layer propagation.

---

## 6. Demos & Acceptance

**Image moving‑dot demo** (28×28):  
- Build a Region with `InputLayer2D → hidden (E/I/M) → OutputLayer2D`.  
- Drive a moving dot for 20 ticks; print every 5 ticks:
  - delivered_events, output_mean, output_nonzero.  
- **Acceptance ranges** (sanity):  
  - `delivered_events > 0` by tick 5,  
  - `0.0 < output_mean < 0.5`,  
  - `output_nonzero` grows then stabilizes (not 0, not width*height).

---

## 7. Implementation Order for Codex

1) **Weight** with T0/T2 + `reinforce` (+ unit tests).
2) **Neuron base** with fields and no‑op `onOutput` (+ test firedLast/lastInputValue bookkeeping).
3) **LateralBus** with decay.
4) **InputNeuron / OutputNeuron** (single‑slot) + minimal **Layer** that respects the firing path.
5) **InputLayer2D / OutputLayer2D** + **end_tick** EMA.
6) **Region** with tracts, input binding, **tick_image** convenience.
7) **Excitatory/Inhibitory/Modulatory** neuron types tied to bus semantics.
8) **Demos** and unit tests (per §5).

---

## 8. Non‑functional Requirements

- **Readability over cleverness** (especially C++ and Mojo).
- **Determinism** in demos (prefer fixed patterns over RNG unless seeded).
- **Zero global state**; Region is the state owner.
- **Logging hooks** but keep stdout minimal by default.

---

## 9. Out of Scope (v2)

- Persistent storage/serialization.
- GPU kernels / vectorization (Mojo‑GPU staging optional in v3).
- Cross‑region global neuromodulators.
- Learned wiring policies (use simple random connect for now).

---

## 10. Constants (recommended defaults)

```
beta = 0.01
adaptSpeed = 0.02
targetRate = 0.05
epsilonFire = 0.01
t0Slack = 0.02
slotHitSaturation = 10000
outputSmoothing = 0.20
inhibitionDefault = 1.00  # neutral
modulationDefault = 1.00  # neutral
```
**Mojo:** declare constants with `alias`.

---

## 11. Deliverables (per language)

- Source files per layout in §4.
- Build/run instructions (README or comments).
- Unit tests that demonstrate §5 cases.
- Demo that satisfies §6 acceptance.
- Short CHANGELOG describing any deviations from this spec.

**Date:** 2025-08-09