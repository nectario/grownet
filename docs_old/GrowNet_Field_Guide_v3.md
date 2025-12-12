
# GrowNet — Engineer’s Field Guide (v3 Baseline)

**Audience:** software engineers & data scientists  
**Scope:** architecture, cross‑language contract, coding style, debugging, benchmarks, and open items.  
**Gold reference:** **Java** implementation. C++ and Python/Mojo mirror the same semantics.

> Use this as the **handoff pack** to start a fresh thread. It summarizes the decisions and the code shape we converged on, so you can quickly re‑establish state and continue the work.

---

## 1) Project snapshot

- **Goal:** biologically inspired, slot‑based neural fabric where synapses and “slots” (discretized input regimes) adapt over time. Support multiple languages (Java, C++, Python, Mojo) behind a single contract.
- **Design center:** correctness and parity across languages. Java is the **gold** copy for semantics; other languages are isomorphic.
- **Recent highlights**
  - `RegionMetrics` **extracted** from `Region` (Java): `ai.nektron.grownet.metrics.RegionMetrics` with private fields and increment/add helpers.
  - `Region.tick(...)` / `Region.tickImage(...)` produce the same metrics shape across languages.
  - C++ `RegionMetrics` now exposes `incDeliveredEvents()`, `addSlots()`, `addSynapses()` to match Java.
  - Python & Mojo: function/method **snake_case**; **no leading underscores** in field names; each neuron in its own file; `input_layer_2d.py` / `output_layer_2d.py`.
  - Slotting: `SlotEngine` uses `SlotPolicy` {`FIXED`, `NONUNIFORM`, `ADAPTIVE`} and percent‑delta binning for ADAPTIVE.
  - Benchmark harness & `config.yaml` described for end‑to‑end and microbenchmarks.
  - Debugging workflow defined to follow a **single tick** through neuron → layer → region with strategic breakpoints (Java, Python).

---

## 2) Core model

### 2.1 Terminology
- **Weight:** strength/threshold plus book‑keeping (`firstSeen`, thresholds).
- **Synapse:** directed edge from `source` neuron to `target` neuron with a `Weight` and a `feedback` flag.
- **Slot:** a discrete “bin” of input regime; each neuron holds a map of `slot_id → Weight`.
- **SlotEngine:** policy that selects/creates a slot based on input deltas or fixed partitions.
- **Neuron:** base type that owns slots, outgoing synapses, last input value, and firing logic.
  - Subtypes: `ExcitatoryNeuron`, `InhibitoryNeuron`, `ModulatoryNeuron`, `InputNeuron`, `OutputNeuron`.
- **Layer:** ordered list of neurons; fans out activity (wire helper, forward, end_tick).
- **Region:** owns layers, input/output port binding, random wiring helpers, and the tick/prune orchestration.
- **Buses:** `RegionBus` (region‑wide signals), `LateralBus` (modulation/inhibition available during `on_input` and `fire`).

### 2.2 Data ownership
- Layers **own** neurons.
- Neurons **own** outgoing synapses (edges) and slot map.
- Region **owns** layers and provides `connect_layers` utilities to create synapses between layers.
- Buses are passed by reference where needed (language‑specific patterns apply).

---

## 3) Canonical APIs (language‑agnostic shape)

### 3.1 Region (public surface)

```
Region(name: string)
add_layer(excitatory_count: int, inhibitory_count: int, modulatory_count: int) -> int
connect_layers(source_index: int, dest_index: int, probability: float, feedback: bool=false) -> int
bind_input(port: string, layer_indices: list[int]) -> None
bind_output(port: string, layer_indices: list[int]) -> None
pulse_inhibition(factor: float) -> None   # reserved in some languages
pulse_modulation(factor: float) -> None   # reserved in some languages
tick(port: string, value: float) -> RegionMetrics
tick_image(port: string, frame: 2D array[float]) -> RegionMetrics
prune(synapse_stale_window: long, synapse_min_strength: float) -> PruneSummary
get_name() -> string
get_layers() -> list[Layer]
get_bus() -> RegionBus

RegionMetrics {
  deliveredEvents: long,
  totalSlots: long,
  totalSynapses: long
}

PruneSummary {
  prunedSynapses: long,
  prunedEdges: long   # reserved for tract‑level pruning
}
```

> **Notes**
> - Method names differ by language casing conventions (Java/C++: camelCase; Python/Mojo: snake_case), **semantics are identical**.
> - `tick_image` is available where `InputLayer2D` exists (Java, C++, Python, Mojo).

### 3.2 Layer (essentials)
```
Layer(excitatory_count: int, inhibitory_count: int, modulatory_count: int)
get_neurons() -> list[Neuron]
wire_random_feedforward(probability: float) -> None
wire_random_feedback(probability: float) -> None
forward(value: float) -> None
end_tick() -> None
```

### 3.3 Neuron (essentials)
```
Neuron(id: string, bus: LateralBus/RegionBus, slot_config: SlotConfig, slot_limit: int=-1)
connect(target: Neuron, feedback: bool=false) -> Synapse
on_input(value: float) -> bool              # returns fired?
fire(input_value: float) -> None            # subtype‑specific behavior
end_tick() -> None
prune_synapses(stale_window: long, min_strength: float) -> int
get_slots() -> map[int, Weight]
get_outgoing() -> list[Synapse]
```

### 3.4 Slotting
```
SlotPolicy: { FIXED, NONUNIFORM, ADAPTIVE }

SlotConfig {
  policy: SlotPolicy
  # policy‑specific fields (e.g. fixed bin count, non‑uniform thresholds, adaptive epsilon)
}
SlotEngine(cfg: SlotConfig)
slot_id(last_input: float, current_input: float, known_slots: int) -> int
select_or_create_slot(neuron: Neuron, input_value: float) -> Weight
```

---

## 4) Cross‑language parity notes

### 4.1 Java (gold)
- `RegionMetrics` moved to `ai.nektron.grownet.metrics.RegionMetrics` with private fields and helpers:
  - `incDeliveredEvents()`; `addSlots(long)`; `addSynapses(long)`; plus standard getters/setters.
- `Region.tick/tickImage` use those helpers—no direct field access.
- `Region.PruneSummary` remains an inner static class with `prunedSynapses`, `prunedEdges`.

**Debugging path (Java):**
- Typical breakpoints:
  - `Region.tick` before forwarding to entry layers.
  - `Layer.forward`
  - `Neuron.onInput` and subtype `fire`
  - `Synapse.transmit` (if present) / wherever weights are reinforced
  - `Layer.endTick`
- Use IntelliJ “Drop frame” and “Smart step into” to walk a single tick.

### 4.2 C++
- `RegionMetrics` exposes `incDeliveredEvents()`, `addSlots()`, `addSynapses()` to match Java shape.
- Include `<stdexcept>` for out‑of‑range checks in `Region::connectLayers`/`Region::tickImage`.
- Where dynamic casting was used, ensure the base is polymorphic (virtual dtor) **or** avoid dynamic casts via explicit type paths.
- `SlotEngine`/`SlotPolicy` are distinct types; ensure headers are included before `Neuron.h` as needed.
- Prefer `std::unique_ptr<Neuron>` in containers, and `std::shared_ptr` only when shared ownership is necessary.

**Debugging path (C++):** set breakpoints in `Region::tick`, `Layer::forward`, `Neuron::onInput`, `SlotEngine` methods, and `endTick`. Build with `-g -O0` for clarity.

### 4.3 Python
- **Naming:** all functions/methods in `snake_case`. **Fields do not start with `_`** (but snake_case is used).
- **Layout:**
  - One file per neuron class (e.g., `excitatory_neuron.py`, `inhibitory_neuron.py`, `modulatory_neuron.py`, `input_neuron.py`, `output_neuron.py`).
  - `input_layer_2d.py`, `output_layer_2d.py` for shape‑aware layers.
  - Avoid `@dataclass` as requested; write explicit `__init__` and accessors when needed.
- Parity with Java for `region.tick/tick_image` and `RegionMetrics` helpers.

**Debugging path (Python):** use `breakpoint()` (or VS Code/PyCharm) in `region.tick`, `layer.forward`, `neuron.on_input`, and `output_neuron.end_tick` to watch decay.

### 4.4 Mojo
- **Rules:** use `fn` for all functions/methods; always annotate parameter and return types; use `mut` for pass‑by‑mutation (no `inout`).
- **Syntax:** Mojo changes quickly—avoid exotic features; prefer `struct`‑like definitions with `var` fields and `fn` methods.
- **Parity:** mirror Python file layout and method names (snake_case). Align semantics with Java/C++.
- Ensure `tick`/`tick_image` return a metrics struct mirroring Java’s getters/adders.
- Use explicit numeric types (`Float64`, `Int`, etc.) and containers that Mojo supports today.

---

## 5) Contract (MASTER)

**Purpose:** cross‑language source‑of‑truth. (YAML variant kept in repo as `grownet_protocol.yaml`).

```
contract: GrowNet
version: 3
language_targets: [java, cpp, python, mojo]

types:
  RegionMetrics:
    fields:
      deliveredEvents: long
      totalSlots: long
      totalSynapses: long
    methods:
      - incDeliveredEvents()
      - addSlots(amount: long)
      - addSynapses(amount: long)

  PruneSummary:
    fields:
      prunedSynapses: long
      prunedEdges: long

  SlotPolicy: [FIXED, NONUNIFORM, ADAPTIVE]

apis:
  Region:
    ctor: Region(name: string)
    methods:
      - addLayer(excitatoryCount: int, inhibitoryCount: int, modulatoryCount: int) -> int
      - connectLayers(sourceIndex: int, destIndex: int, probability: double, feedback: bool=false) -> int
      - bindInput(port: string, layerIndices: int[]) -> void
      - bindOutput(port: string, layerIndices: int[]) -> void
      - tick(port: string, value: double) -> RegionMetrics
      - tickImage(port: string, frame: double[height][width]) -> RegionMetrics
      - prune(synapseStaleWindow: long, synapseMinStrength: double) -> PruneSummary
      - getName() -> string
      - getLayers() -> Layer[]
      - getBus() -> RegionBus
```

> Keep this contract **in sync** with the Java gold copy. Other languages should implement the same surface (casing may differ).

---

## 6) Build & test quick start

**Java**
- `mvn test` / `gradle test`
- Example: `TestSingleTick.java` drives one neuron through `Region.tick` and asserts metrics counts.

**C++**
- CMake with C++17: `-std=c++17 -Wall -Wextra -Wpedantic`
- Targets: `grownet` (library), `region_demo` (sample).

**Python**
- Layout: `src/grownet_py/` (or preferred package name); unit tests under `tests/`.
- Standard library only (no dataclasses).

**Mojo**
- Keep files minimal; use `mojo run` on small demos.
- Be explicit with types; pass mutable values with `mut`.

---

## 7) Debugging recipes (single‑tick story)

1. **Bind** an input port to a single entry layer:
   - Java: `region.bindInput("scalar", List.of(layerIndex));`
   - Python: `region.bind_input("scalar", [layer_index])`
2. **Wire** a small network with `connectLayers` probability ~1.0 between consecutive layers.
3. **Breakpoints**:
   - Region: on `tick` before forwarding.
   - Layer: on `forward` (watch value fan‑out).
   - Neuron: on `on_input` and then subtype `fire` (watch `firedLast`, slot selection, weight updates).
   - Output layer: on `end_tick` to see decay or aggregations.
4. **Step through** one tick and record slot/weight changes in metrics.

---

## 8) Benchmark harness

- **Metrics**: end‑to‑end latency (`tick` wall‑time), events delivered, total slots/synapses; optional micro‑benchmarks for `SlotEngine` and `prune`.
- **Config (`config.yaml`)** (example):
  ```yaml
  runs: 5
  warmup_ticks: 1000
  measure_ticks: 5000
  network:
    layers:
      - { excitatory: 64, inhibitory: 16, modulatory: 8 }
      - { excitatory: 64, inhibitory: 16, modulatory: 8 }
    wiring:
      - { source: 0, dest: 1, probability: 0.2, feedback: false }
    bindings:
      input: { port: scalar, layers: [0] }
  implementations:
    - java
    - cpp
    - python
    - mojo
  ```
- **Outputs**: CSV/JSON with per‑language medians, p95, and effective throughput.

---

## 9) Coding style & conventions

- **Naming:**
  - Java/C++: camelCase methods/fields; classes in PascalCase.
  - Python/Mojo: snake_case for functions/methods; **fields do not start with `_`**.
- **Variables:** prefer descriptive names over single letters (`neuron`, `probability`, `slot_id`, etc.).
- **APIs:** no hidden singletons; pure functions where possible; pass dependencies explicitly.
- **Randomness:** use a **seeded** RNG in demos/tests for determinism.
- **Docs:** brief header comment per type; public methods with one‑line summaries.
- **Testing:** assert both behavior (firing) and counters (metrics).

---

## 10) Migration / parity checklist

- [ ] RegionMetrics extracted & used via helpers in **all** languages.
- [ ] `tick`/`tick_image` parity (same counters, same order of operations).
- [ ] `connect_layers` returns edge count (consistent semantics).
- [ ] Input/Output 2D layers available in languages that support them.
- [ ] SlotEngine policy enum and selection logic present and tested.
- [ ] Bench harness reads shared `config.yaml` shape.
- [ ] Breakpoint/demo projects compile & run.
- [ ] No single‑letter variable names in new code paths.

---

## 11) Open items / next thread seed

- Region‑to‑Region connectivity and **growth** orchestration (per the high‑level diagram).
- Serialization format (saving region/layer/neuron state and slot maps).
- Concurrency policy (tick batching, tract queues) and lock strategy.
- Visualization hooks (slot and synapse distributions per layer).
- Extended pruning (tract‑level edges; criteria beyond strength/stale).

---

## 12) Appendix A — Minimal code cues (language‑neutral)

**RegionMetrics helpers** (shape, not verbatim):
```
incDeliveredEvents()
addSlots(delta: long)
addSynapses(delta: long)
```

**Region tick (shape):**
```
m = RegionMetrics()
for entry_layer in input_ports[port]:
    layers[entry_layer].forward(value)
    m.incDeliveredEvents()
for layer in layers: layer.endTick()
for layer in layers:
    for neuron in layer.neurons:
        m.addSlots(len(neuron.slots))
        m.addSynapses(len(neuron.outgoing))
return m
```

---

## 13) Practical notes

- Some previously uploaded archives may have expired; if you need me to re‑load any file in a fresh thread, please re‑attach it.
- When starting the new thread, paste:
  1) This document’s link, and
  2) The exact language pair you want to work on next (e.g., “Mojo ↔ Python parity for Input/Output 2D”).

---

**End of document.**
