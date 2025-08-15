Below is a single **unified, up‑to‑date design spec** that merges everything we’ve built and refined across Java (gold copy), C++, Python and Mojo. It supersedes prior versions and is written for software engineers and data scientists.

------

# GrowNet — Unified Design Spec (v2)

**Status:** Draft for implementation parity
 **Primary audience:** Software engineers & data scientists
 **Scope:** Algorithm, data model, buses, APIs, language parity, benchmarks, and protocol

------

## 1) Executive Summary

GrowNet is an event‑driven neural system that **grows, adapts, and prunes** a graph of mixed‑type neurons. Each neuron is a container of **independent threshold sub‑units (“slots”)**. Learning is **local** (no global error/backprop), driven by **non‑linear reinforcement** gated by **lateral inhibition** and **neuromodulation** on a per‑layer bus. The network is organized into **layers** connected by **tracts**, all orchestrated by a **region** that receives input events on named ports and advances time in **ticks**. This design consolidates the “Theory of Change” with the concrete region API (construction, wiring, ticking, pruning) used in the current codebases.  

------

## 2) Architectural Overview

```
                +--------------------  event stream  -------------------+
                |                                                       |
                v                                                       |
   +-----------------------+    feedforward / feedback     +-----------------------+
   |       Layer k         | --(Tract)-------------------->|       Layer k+1       |
   |  (Excit / Inhib / Mod)|<---(optional feedback Tract)--|  (Excit / Inhib / Mod)|
   +-----------------------+                                +-----------------------+
           ^                                                                |
           |         LateralBus: inhibition γ(t) and modulation κ(t)        |
           +---------------------- back-prop-free learning -----------------+
```

- **Neuron = slots:** a neuron fires if *any* of its slots crosses its adaptive threshold (logical OR).
- **Three neuron phenotypes:**
  - **Excitatory:** propagates spikes to downstream synapses.
  - **Inhibitory:** increases layer‑local inhibition level for ΔT timesteps.
  - **Modulatory:** scales learning rate (reinforcement step) for ΔT timesteps.
     These behaviors are delivered via a per‑layer **LateralBus** and are the core of the “Theory of Change”. 
- **Region orchestration:** Regions hold layers, tracts, named I/O port bindings, and implement **tick** (scalar inputs) plus maintenance (e.g., **prune**). The canonical **Region** surface (add/connect/bind/tick/pulse/prune) is the cross‑language reference. 

------

## 3) Data Model

### 3.1 Weight (slot state)

Each slot maintains its own plasticity and threshold state:

| Field       | Type  | Meaning                                        |
| ----------- | ----- | ---------------------------------------------- |
| `strength`  | float | Synaptic efficacy (clamped to [−1, +1]).       |
| `hitCount`  | int   | Saturates (e.g., 10k) to freeze weight growth. |
| `theta`     | float | **Adaptive threshold** for this slot.          |
| `emaRate`   | float | Exponential moving average of recent fires.    |
| `firstSeen` | bool  | Whether T0 “imprint” has been executed.        |

> **Why here?** Adaptive θ is kept **inside Weight** so slot dynamics are fully local (design choice carried over into all languages). 

### 3.2 Neuron (base)

Common state and behavior:

| Field            | Type                     | Meaning                                 |
| ---------------- | ------------------------ | --------------------------------------- |
| `slots`          | map<int, Weight>         | Slot id → per‑slot state.               |
| `outgoing`       | vector (or equivalent)   | Downstream synapses.                    |
| `haveLastInput`  | bool                     | Whether we saw an input last tick.      |
| `lastInputValue` | double                   | Most recent input received.             |
| `typeTag`        | enum {EXCIT, INHIB, MOD} | Runtime behavior switch.                |
| `bus`            | LateralBus*              | Pointer to layer‑local bus (inhib/mod). |

### 3.3 LateralBus (per layer)

```text
inhibitionLevel: float   # decays toward 0
modulationFactor: float  # resets toward 1
```

- All neurons read from this bus during **reinforce** (to scale updates) and **fire** (to apply lateral inhibition). 

### 3.4 RegionBus (inter‑layer)

A light abstraction for region‑level pulses (e.g., temporary external events). Region exposes helpers like `pulseInhibition()` and `pulseModulation()` that set bus‑level factors for the next tick. 

------

## 4) Algorithms

### 4.1 Slot selection and IDs (SlotEngine)

- **Goal:** route the current input into a stable slot index.
- **Default policy:** **percent‑delta** between the last input and the current input, binned into **fixed** or **non‑uniform** ranges.
- **Policies:**
  - **FIXED:** uniform binning by percent‑delta.
  - **NONUNIFORM:** domain‑aware bins (e.g., finer resolution near 0 %).
  - **ADAPTIVE:** (optional) bins that shift based on empirical distribution.

> These policies are reflected in our SlotEngine across languages and are used by the neuron’s `on_input()` path to pick/create the slot. (In C++ the SlotEngine is composed inside `Neuron`.) The policy selection is implementation detail; the behavior contract is “percent‑delta → slot id”. (Consolidated from code and unit fixes.)

### 4.2 Local learning (per slot)

```
effectiveStep = baseStep * bus.modulationFactor
if weight.hitCount < HIT_SAT:
    weight.strength = smoothClamp(weight.strength + effectiveStep, -1, +1)
    weight.hitCount += 1
```

### 4.3 Adaptive threshold (T0 imprint + T2 control)

```
if not weight.firstSeen:
    weight.theta = abs(input) * (1 + EPS)  # T0 imprint
    weight.firstSeen = True

fired = (weight.strength > weight.theta)

weight.emaRate = (1 - BETA) * weight.emaRate + BETA * (1 if fired else 0)
weight.theta  += ETA * (weight.emaRate - R_STAR)
```

- This matches the **slot‑local** θ adaptation described in the theory document. 

### 4.4 Firing behavior

```
if any slot fires:
    if typeTag == EXCIT:  propagate downstream
    if typeTag == INHIB:  bus.inhibitionLevel = γ (decays)
    if typeTag == MOD:    bus.modulationFactor = κ (decays/resets)
```

- Inhibition can also attenuate downstream slot strengths or bias thresholds depending on profile; the current default is attenuation via the shared bus. 

------

## 5) Components & APIs

### 5.1 Region (canonical surface)

**Construction & wiring**

- `addLayer(excitatoryCount, inhibitoryCount, modulatoryCount) -> int`
- `connectLayers(sourceIndex, destIndex, probability, feedback=false) -> Tract&`
- `bindInput(portName, [layerIndices])`
- `bindOutput(portName, [layerIndices])`

**Tick & pulses**

- `tick(portName, value) -> RegionMetrics` (scalar events)
- `pulseInhibition(factor)` / `pulseModulation(factor)` (one‑shot region‑wide pulses)

**Maintenance**

- `prune(synapseStaleWindow, synapseMinStrength, tractStaleWindow, tractMinStrength) -> PruneSummary`

**Accessors**

- `getName()`, `getLayers()`, `getTracts()`, `getBus()`

**Metrics structs**

- `RegionMetrics { deliveredEvents, totalSlots, totalSynapses }`
- `PruneSummary  { prunedSynapses, prunedEdges }`

> These names and signatures are the contract we mirror across languages; they come from the C++ header and align with the Java gold copy. 

> **Note:** Image support is implemented by **shape‑aware layers** (`InputLayer2D`, `OutputLayer2D`), with per‑language helpers. Java additionally exposes `tickImage(port, frame)` for convenience; in C++/Python/Mojo we call `forward_image()` on the input layer(s) bound to that port and then run `end_tick()` across layers (keeps Region’s surface minimal). (This is a harmonization detail across languages.)

### 5.2 Layer

- Holds **mixed populations** (Excit/Inhib/Mod) that share a **LateralBus**.
- **Wiring helpers:** `wireRandomFeedforward(p)`, `wireRandomFeedback(p)` (intra‑layer).
- **Tick‑phase methods:**
  - `forward(value)` — run one scalar event through all neurons.
  - `end_tick()` — decay bus levels, finalize per‑neuron transient state.

### 5.3 Neuron hierarchy

- **Neuron (base):** slot selection (`SlotEngine`), reinforcement, firing decision, and event hooks.
- **ExcitatoryNeuron:** default `fire` = propagate to outgoing synapses.
- **InhibitoryNeuron:** `fire` raises `inhibitionLevel` on the **LateralBus**.
- **ModulatoryNeuron:** `fire` scales `modulationFactor` on the **LateralBus**.
- **InputNeuron / OutputNeuron:** thin wrappers used by 2D layers. Output neurons keep a `last_emitted` value and apply a per‑tick decay in `end_tick()`.

### 5.4 Tract

- A connection bundle between a **source layer** and a **destination layer**.
- Fans out from each source neuron to a random subset of destination neurons with probability `p` (build‑time), with an optional **feedback** flag.

------

## 6) 2D I/O Layers (shape‑aware)

### 6.1 InputLayer2D

- Holds `height × width` **InputNeurons**.
- `forward_image(frame: double[H][W])`: each neuron receives the scalar at `(y, x)` and runs the standard `on_input` path.

### 6.2 OutputLayer2D

- Holds `height × width` **OutputNeurons** that record `last_emitted` amplitude.
- `end_tick()` snapshots each neuron’s `last_emitted` into a `frame[H][W]` buffer (and applies decay).
- `get_frame() -> double[H][W]`: returns the latest rendered frame.

> These layers are thin façades over the generic neuron logic; their existence is a portability affordance so we can drive image demos identically in Java, C++, Python, and Mojo.

------

## 7) Growth & Pruning

### 7.1 Growth

- **On‑demand slot creation:** if a percent‑delta falls into a previously unseen bin, the neuron **creates** a new slot (`Weight`) lazily.
- **Fan‑out:** tracts pre‑allocate synapses by probability; later we can allow dynamic synapse creation (guarded by caps) if required.

### 7.2 Pruning

- **Per‑synapse:** remove stale or weak synapses using `(staleWindow, minStrength)`.
- **Per‑tract:** remove entire tracts that have not carried signal or whose aggregate strength falls below thresholds.
- **Report:** `PruneSummary { prunedSynapses, prunedEdges }`. 

------

## 8) Region Lifecycle

1. **Construction:** create a `Region(name)`, add layers, connect layers, bind I/O ports. 
2. **Tick (scalar):** `tick(port, value)` delivers to all input‑bound layers for `port`; each layer runs `forward(value)`; all layers then run `end_tick()`; return `RegionMetrics`. 
3. **Tick (image):** use `InputLayer2D.forward_image(frame)` on the layers bound to `port`, then `end_tick()`. (Java additionally offers `tickImage`.)
4. **Maintenance:** occasionally call `prune(…)`. 

------

## 9) Cross‑Language Parity

### 9.1 Java (gold copy)

- Source of truth for algorithm semantics and public method shapes (including `tickImage` convenience).

### 9.2 C++

- Mirrors Region API exactly (names/types match the header). **Reference:**
  - `Region`, `RegionMetrics`, `PruneSummary`, `addLayer`, `connectLayers`, `bindInput/Output`, `tick`, `pulseInhibition/Modulation`, `prune`, `getLayers/Tracts/Bus`. 
- `InputLayer2D` / `OutputLayer2D` exist as separate classes; image ticks are done via those layers + `end_tick()`.

### 9.3 Python

- **No `@dataclass`** (explicit `__init__`).
- **Naming:** all module names and methods use **snake_case** with leading underscores for private helpers; every neuron has its **own file** (e.g., `neuron_excitatory.py`, `neuron_inhibitory.py`, `neuron_modulatory.py`).
- No `grownet/` subfolder beneath `python/` (flat package layout under `src/python` as agreed).

### 9.4 Mojo

- Mirrors the Python structure and semantics. Differences:
  - All functions and methods declared with **`fn`**.
  - **All parameter and return types** are explicit.
  - Avoid evolving syntax; prefer standard containers and simple control flow.
- File parity with Python (one file per neuron class, `input_layer_2d.mojo`, `output_layer_2d.mojo`, etc.).

------

## 10) YAML Protocol (control & runs)

A single YAML contract drives **experiments, wiring, and benchmarks** across languages:

```yaml
version: 2
region:
  name: "demo"
  layers:
    - { excitatory: 200, inhibitory: 40, modulatory: 10 }
    - { excitatory: 200, inhibitory: 40, modulatory: 10 }
  tracts:
    - { src: 0, dst: 1, probability: 0.12, feedback: false }
ports:
  input:
    pixels: [0]        # port -> layer indices
  output:
    logits: [1]
slot_engine:
  policy: FIXED        # or NONUNIFORM / ADAPTIVE
  bins: 16
learning:
  base_step: 0.01
  beta_fire_ema: 0.05
  eta_theta: 0.001
  r_star: 0.1
bus:
  inhibition_decay: 0.9
  modulation_decay: 0.9
prune:
  synapse_stale_window: 10000
  synapse_min_strength: 0.05
  tract_stale_window: 10000
  tract_min_strength: 0.05
run:
  ticks: 2000
  inputs:
    kind: scalar|image|file
    port: pixels
    file: "data/mnist_28x28.npy"
```

- These fields cover Region wiring (from the C++ header), SlotEngine policies, learning hyper‑parameters, bus dynamics, and pruning thresholds. 

------

## 11) Benchmarking & Observability

### 11.1 Metrics

- **End‑to‑end latency per tick** (P50/P90/P99).
- **Throughput** (ticks/sec).
- **Micro‑benchmarks**:
  - Slot selection (percent‑delta → bin).
  - Reinforcement update.
  - Fire propagation per synapse.
  - Bus decay.
  - Pruning pass (synapse & tract).
- **Structural metrics** (per tick and per run): `totalSlots`, `totalSynapses`, `deliveredEvents`. (Region reports these natively.) 

### 11.2 Methodology

- Fixed random seeds for wiring and inputs.
- Warmup ticks excluded from measurement.
- CPU affinity optional; record environment (OS, arch, compiler/interpreter version).
- Same YAML across Java/C++/Python/Mojo.

------

## 12) Testing Strategy

1. **Determinism smoke tests:** with fixed seed, ensure slot counts and fire counts are stable within a tolerance (floating‑point drift acceptable across languages).
2. **Conservation tests:** `totalSynapses` increases only via growth; decreases only via prune; never negative. 
3. **Image I/O tests:** `InputLayer2D.forward_image()` then `OutputLayer2D.get_frame()` produces non‑zero output on simple patterns (e.g., single bright pixel).
4. **Bus behavior tests:** inhibitory and modulatory pulses affect subsequent reinforcement and firing as expected and decay back toward neutral.
5. **Pruning tests:** with synthetic inactivity, ensure `prune` returns non‑zero `prunedSynapses`/`prunedEdges` and structure sizes drop accordingly. 

------

## 13) Migration Notes (from earlier v1 docs)

- **Adaptive θ moved into `Weight`:** older code kept thresholds at neuron scope; now each slot adapts independently. 
- **Unified buses:** use `LateralBus` for per‑layer inhibition/modulation and `RegionBus` for region‑wide pulses (APIs exposed in Region). 
- **Image path:** use `InputLayer2D` / `OutputLayer2D` universally; Java may provide `tickImage`, while C++/Python/Mojo drive the image through the input layer then call `end_tick()`.
- **Pruning contract standardized:** windows + minimum strengths for synapses and tracts; returns `PruneSummary`. 
- **Language conventions:** Python/Mojo file layout and naming normalized (snake_case; one neuron per file; no nested `grownet/` folder in Python).

------

## 14) Open Questions

| Topic                            | Options / Notes                                              |
| -------------------------------- | ------------------------------------------------------------ |
| Exact γ/κ defaults               | Tune per dataset; start with 0.7 / 1.5 and decay 0.9 per tick. |
| SlotEngine ADAPTIVE policy       | Keep behind a flag until distribution‑shift tests pass.      |
| Dynamic synapse growth (runtime) | Off by default; consider caps & budgets per neuron.          |
| Multi‑region composition         | Current focus is single region; multi‑region routing API to be designed later. |

------

## 15) Reference Snippets (language‑agnostic)

**Region main loop (scalar):**

```
metrics = {deliveredEvents: 0, totalSlots: 0, totalSynapses: 0}
for layerIndex in inputPorts[port]:
    layers[layerIndex].forward(value)
    metrics.deliveredEvents += 1

for layer in layers:
    layer.end_tick()
    metrics.totalSlots    += sum(len(n.slots) for n in layer.neurons)
    metrics.totalSynapses += sum(len(n.outgoing) for n in layer.neurons)

return metrics
```

> Mirrors the Region metrics contract we rely on across languages. 

**Output layer render:**

```
for idx, neuron in enumerate(output_neurons):
    neuron.end_tick()                   # apply decay, finalize output
    frame[idx // width][idx % width] = neuron.last_emitted
```

------

## 16) Directory Layout (normative)

```
/src
  /java/ai/nektron/grownet/...
  /cpp/grownet/...
  /python/
    math_utils.py
    slot_engine.py
    weight.py
    neuron_base.py
    neuron_excitatory.py
    neuron_inhibitory.py
    neuron_modulatory.py
    input_layer_2d.py
    output_layer_2d.py
    layer.py
    region.py
    tract.py
  /mojo/
    weight.mojo
    neuron_base.mojo
    neuron_excitatory.mojo
    neuron_inhibitory.mojo
    neuron_modulatory.mojo
    input_layer_2d.mojo
    output_layer_2d.mojo
    layer.mojo
    region.mojo
    tract.mojo
/docs
  GrowNet_Design_Spec_v2.md
  (generated from this document)
```

---

## 17) Appendix A: Canonical Region API (from C++ header)

Authoritative cross‑language **shape** for `Region` (exact signatures taken from C++). Other languages map to this shape (see Appendix B for naming in Python/Mojo).&#x20;

* `Region(std::string name)`
* `int addLayer(int excitatoryCount, int inhibitoryCount, int modulatoryCount)`
* `Tract& connectLayers(int sourceIndex, int destIndex, double probability, bool feedback=false)`
* `void bindInput(const std::string& port, const std::vector<int>& layerIndices)`
* `void bindOutput(const std::string& port, const std::vector<int>& layerIndices)`
* `void pulseInhibition(double factor)` / `void pulseModulation(double factor)`
* `RegionMetrics tick(const std::string& port, double value)`
* `PruneSummary prune(long long synapseStaleWindow=10000, double synapseMinStrength=0.05, long long tractStaleWindow=10000, double tractMinStrength=0.05)`
* Accessors: `getName()`, `getLayers()`, `getTracts()`, `getBus()`
* `RegionMetrics { deliveredEvents, totalSlots, totalSynapses }`
* `PruneSummary { prunedSynapses, prunedEdges }`

> Source of truth for these signatures: `Region.h`.&#x20;

---

## 18) Appendix B: Contract Protocol (MASTER SPEC v3)

> This YAML is the master, single source‑of‑truth contract for GrowNet v3.
> Behavior‑level rationale (slot learning, bus semantics, neuron roles) follows the “Theory of Change” document.&#x20;

```yaml
# ============================================================================
# GrowNet Contract — MASTER SPEC (v3)
# ============================================================================

meta:
  version: 3.0.0
  status: master
  last_updated_utc: 2025-08-15
  gold_language: java
  mirrors:
    - cpp
    - python
    - mojo
  rationale_refs:
    - theory_of_change  # design rationale and behavior overview

conventions:
  numeric:
    float_range: [-inf, +inf]
    weight_strength_range: [-1.0, +1.0]
    default_modulation_factor: 1.0
    default_inhibition_level: 0.0
  naming:
    java_package: "ai.nektron.grownet"
    cpp_namespace: "grownet"
    python_module_prefix: ""        # no 'grownet/' folder under python
    python_method_style: "snake_case_with_leading_underscore"  # e.g., _tick
    mojo_method_style: "snake_case_with_leading_underscore"
  files_and_layout:
    cpp:
      root: "src/cpp"
      build: "CMake (C++17)"
    python:
      root: "src/python"
      files:
        - "math_utils.py"
        - "weight.py"
        - "slot_engine.py"
        - "lateral_bus.py"
        - "region_bus.py"
        - "synapse.py"
        - "neuron_base.py"
        - "neuron_excitatory.py"     # file per neuron class
        - "neuron_inhibitory.py"
        - "neuron_modulatory.py"
        - "input_neuron.py"
        - "output_neuron.py"
        - "layer.py"
        - "tract.py"
        - "region.py"
        - "input_layer_2d.py"        # specific filenames required
        - "output_layer_2d.py"
    mojo:
      root: "src/mojo"
      mirrors_python_files: true     # mirrors python split & names
  threading_and_time:
    tick_model: "two_phase"
    bus_decay_per_tick: true
    inhibition_is_ephemeral: true
    modulation_resets_each_tick: true

types:
  # ----------------------------- Core math & utils ---------------------------
  Weight:
    fields:
      strength: float                # clamped to [-1, 1]
      hit_count: int                 # capped (e.g., 10000) to freeze learning
      theta: float                   # adaptive threshold
      ema_rate: float                # exponential moving average of fires
      seen_first: bool               # T0 imprint executed?
    methods:
      _reinforce(modulation_factor: float) -> None
      _update_threshold(input_value: float) -> bool   # returns fired?
      _decay_inhibition(inhibition_factor: float) -> None   # typically scales strength
  SlotEngine:
    purpose: "Map (last_input, current_input) → slot_id; retrieve or create slot."
    methods:
      _slot_id(last_input: float, current_input: float, known_slots: int) -> int
      _select_or_create_slot(neuron: "Neuron", input_value: float) -> "Weight"
  LateralBus:
    fields:
      inhibition_level: float        # decays toward 0 each tick
      modulation_factor: float       # resets to 1 each tick
    methods:
      _set_inhibition(factor: float) -> None
      _set_modulation(factor: float) -> None
      _decay() -> None
  RegionBus:
    purpose: "Cross-layer bus used by Region (owner of LateralBus per layer or shared)."
    fields:
      inhibition_factor: float
      modulation_factor: float
    methods:
      _set_inhibition_factor(factor: float) -> None
      _set_modulation_factor(factor: float) -> None
      _decay() -> None

  # ----------------------------- Connectivity -------------------------------
  Synapse:
    fields:
      source: "Neuron"
      target: "Neuron"
      weight_ref: "Weight"           # shared with target's slots store
      is_feedback: bool
    methods:
      _propagate(amplitude: float) -> None

  # ----------------------------- Neurons ------------------------------------
  Neuron:
    abstract: true
    common_fields:
      neuron_id: string
      bus: "LateralBus"
      slot_engine: "SlotEngine"
      slot_limit: int                # -1 means unbounded
      last_input_value: float
      have_last_input: bool
      slots: dict<int, "Weight">     # bins keyed by slot_id
      downstream: list["Synapse"]
    hooks:
      _fire_hooks: list<fn("Neuron", float) -> None>   # user / Tract hook
    common_methods:
      _on_input(value: float) -> bool                  # returns fired?
      _on_output(amplitude: float) -> None
      _connect(target: "Neuron", feedback: bool=false) -> "Synapse"
      _register_fire_hook(hook: fn("Neuron", float) -> None) -> None
      _end_tick() -> None
    subclass_contract:
      # subclasses can override _fire() to implement behavior differences
      _fire(amplitude: float) -> None

  ExcitatoryNeuron:
    extends: Neuron
    behavior: "On fire: propagate to downstream via Synapse::_propagate"
  InhibitoryNeuron:
    extends: Neuron
    behavior: "On fire: set layer/region bus inhibition for a tick"
    parameters:
      gamma: float   # 0 < gamma < 1
  ModulatoryNeuron:
    extends: Neuron
    behavior: "On fire: scale learning rate via bus modulation"
    parameters:
      kappa: float   # e.g., 1.0 (no change) to >1 (boost)
  InputNeuron:
    extends: Neuron
    behavior: "Drive a single slot with external input; emits only if slot beats theta"
  OutputNeuron:
    extends: Neuron
    extra_fields:
      last_emitted: float
      smoothing: float
    methods:
      _get_output_value() -> float
      _end_tick() -> None            # e.g., decay last_emitted by (1 - smoothing)
    behavior: "Captures output for read‑back (image/array writers, etc.)"

  # ----------------------------- Layers -------------------------------------
  Layer:
    fields:
      neurons: list["Neuron"]
      bus: "LateralBus"
    methods:
      _wire_random_feedforward(probability: float) -> None
      _wire_random_feedback(probability: float) -> None
      _forward(value: float) -> None
      _end_tick() -> None
      # Optional shim for shape-aware layers; base Layer need not implement:
      _propagate_from(source_index: int, value: float) -> None
  InputLayer2D:
    extends: Layer
    fields:
      height: int
      width: int
      gain: float
      epsilon_fire: float
    methods:
      _index(y: int, x: int) -> int
      _forward_image(frame: list[list[float]]) -> None     # drives per-pixel inputs
      _propagate_from(source_index: int, value: float) -> None
  OutputLayer2D:
    extends: Layer
    fields:
      height: int
      width: int
      frame: list[list[float]]
      smoothing: float
    methods:
      _index(y: int, x: int) -> int
      _propagate_from(source_index: int, value: float) -> None
      _end_tick() -> None          # fills frame[y][x] from per-neuron _get_output_value()
      _get_frame() -> list[list[float]]

  # ----------------------------- Region & Tract ------------------------------
  Tract:
    fields:
      source: "Layer"
      dest: "Layer"
      bus: "RegionBus"
      feedback: bool
      connections: list["Synapse"]
    methods:
      _fanout_random(probability: float) -> int          # number of edges created
      _on_source_fired(neuron: "Neuron", amplitude: float) -> None
  RegionMetrics:
    fields:
      deliveredEvents: int
      totalSlots: int
      totalSynapses: int
  PruneSummary:
    fields:
      prunedSynapses: int
      prunedEdges: int
  Region:
    constructors:
      - (name: string)
    methods_canonical_shape:         # exact from C++/Java shape
      addLayer(excitatoryCount: int, inhibitoryCount: int, modulatoryCount: int) -> int
      connectLayers(sourceIndex: int, destIndex: int, probability: float, feedback: bool=false) -> "Tract"
      bindInput(port: string, layerIndices: list<int>) -> None
      bindOutput(port: string, layerIndices: list<int>) -> None
      pulseInhibition(factor: float) -> None
      pulseModulation(factor: float) -> None
      tick(port: string, value: float) -> "RegionMetrics"
      prune(synapseStaleWindow: long, synapseMinStrength: float, tractStaleWindow: long, tractMinStrength: float) -> "PruneSummary"
      getName() -> string
      getLayers() -> list["Layer"]
      getTracts() -> list["Tract"]
      getBus() -> "RegionBus"
    methods_python_mojo_mapping:
      _add_layer              : addLayer
      _connect_layers         : connectLayers
      _bind_input             : bindInput
      _bind_output            : bindOutput
      _pulse_inhibition       : pulseInhibition
      _pulse_modulation       : pulseModulation
      _tick                   : tick
      _prune                  : prune
      _get_name               : getName
      _get_layers             : getLayers
      _get_tracts             : getTracts
      _get_bus                : getBus

behavior:
  tick_semantics:
    description: >
      A tick is two-phase. First, inputs bound to the named port drive their layers
      via Layer::_forward (or shape-aware propagation for 2D layers). Neurons read the
      bus state (inhibition/modulation) when reinforcing slots. Second, on fire, neurons
      enact phenotype-specific behavior (excitatory propagate, inhibitory pulse, modulatory scale).
      End-of-tick, buses decay and OutputLayer2D snapshots frame.  # See Theory of Change
    bus_rules:
      modulation_reads_before_reinforce: true
      inhibition_scales_on_fire_or_read: true
      decay_at_end_of_tick: true
  learning:
    weight_update: "local, non-gradient; clamp to [-1,1]; cap hit_count"
    theta_adaptation: "per-slot adaptive threshold with EMA target rate"
  pruning:
    synapse_policy:
      stale_window_ticks: 10000
      min_strength: 0.05
    tract_policy:
      stale_window_ticks: 10000
      min_strength: 0.05
    returns: "PruneSummary"

language_bindings:
  java:
    package: "ai.nektron.grownet"
    notes:
      - "Java is the gold copy; semantics must not diverge."
  cpp:
    std: "c++17"
    pointers:
      layers: "std::shared_ptr<Layer>"
      tracts: "std::unique_ptr<Tract>"
    header_of_truth: "Region.h"
  python:
    style:
      leading_underscore_for_all_methods: true
      file_per_neuron_class: true
      input_output_layer_filenames:
        - "input_layer_2d.py"
        - "output_layer_2d.py"
    mapping: "See Region.methods_python_mojo_mapping"
  mojo:
    style:
      leading_underscore_for_all_methods: true
      fn_keyword_required: true
      explicit_param_types_required: true
      avoid_exotic_syntax: true
    mapping: "Same as Python"

io_and_ports:
  bind_input:
    description: "Associate a port (string) with one or more layer indices; used by tick(port, value)."
  bind_output:
    description: "Associate a port with layers to be sampled or acted upon after tick."
  shape_aware_layers:
    input_layer_2d: "Consumes 2D frames into per-pixel InputNeurons."
    output_layer_2d: "Produces 2D frame from OutputNeurons via _get_output_value()."

metrics:
  region_metrics:
    deliveredEvents: "number of events delivered this tick"
    totalSlots: "sum of slots across all neurons"
    totalSynapses: "sum of outgoing synapses"
  prune_summary:
    prunedSynapses: "synapses removed"
    prunedEdges: "structural edges removed"

benchmarks:
  guidance:
    latency_end_to_end_ms: true
    per_phase_breakdown: [enqueue_inputs, neuron_update, propagation, bus_decay, snapshot]
    micro: [slot_reinforce_ns, slot_threshold_ns, synapse_propagate_ns]
  harness_entrypoints:
    python: "_bench.py main()"
    cpp:    "region_demo or dedicated bench target"
    java:   "BenchmarkRunner"
    mojo:   "bench.mojo main()"

compatibility:
  float_precision: "double preferred across languages for parity"
  thread_safety: "single-threaded by default; future work item for parallel fanout"
  serialization: "out of scope for v3; keep DTOs small (metrics/prune only)"

versioning:
  current: 3
  changes_since_v2:
    - "Introduced Python/Mojo leading-underscore API to avoid public instability."
    - "Enforced file-per-neuron class in Python/Mojo; explicit names for 2D layers."
    - "Clarified bus decay and modulation/inhibition read/write order."
    - "Hardened Region prune contract (four params, two thresholds)."
    - "Canonicalized Region metrics field names."

compliance_checklist:
  - "C++ Region.h signatures match Appendix A."
  - "Java mirrors semantics of C++ and remains the gold copy."
  - "Python methods all begin with '_' and adhere to file layout rules."
  - "Mojo methods use 'fn', explicit typed params, and '_' prefix."
  - "OutputLayer2D drives frame via per-neuron _get_output_value() in _end_tick()."
  - "Tract registers source neuron hooks to propagate events."
  - "Bus decays exactly once per tick."
```

**Notes & cross‑references**

* Appendix A reflects the **exact** signatures in `Region.h` (C++). Use it as the canonical surface that all languages adapt to (see the per‑language name mapping block above).&#x20;
* Behavioral semantics (local learning; OR‑across‑slots; role of excitatory, inhibitory, modulatory neurons; bus modulation/inhibition timing; two‑phase tick) are aligned with the **Theory of Change** document.&#x20;

---

### What changed from v2 → v3 (summary)

* **Python & Mojo APIs use leading underscores** on all methods/functions, and Mojo uses `fn` with **explicit parameter types**.
* **File‑per‑neuron** rule in Python/Mojo; **no `grownet/` package folder** under `src/python`.
* **Input/Output 2D layer filenames fixed**: `input_layer_2d.py`, `output_layer_2d.py`.
* **Bus semantics** clarified: modulation read before reinforce; inhibition is an ephemeral pulse; both **decay at end‑of‑tick**.
* **Prune contract**: four params (two windows + two thresholds) with well‑defined return DTO.
* **Metrics DTO names**: `deliveredEvents`, `totalSlots`, `totalSynapses` standardized across languages.

If you drop this Appendix A & B directly into your design spec, you’ll have a **self‑contained v3 master contract** that matches the C++ header and the agreed behavior across languages.

### Closing

This spec is intentionally **implementation‑oriented** and **language‑agnostic** in semantics, grounding the high‑level “Theory of Change” (neuronal roles, buses, slot‑local adaptation) with the concrete **Region/Layer/Neuron** APIs and maintenance flows we now standardize across Java, C++, Python, and Mojo. Use this as the single reference for future changes and for validating cross‑language parity. 