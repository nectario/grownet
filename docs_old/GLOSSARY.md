# GrowNet Glossary (v3)

## Core graph concepts

**Region**
 A container of layers and wiring. Orchestrates tick execution, input/output “port” bindings, and maintenance tasks (e.g., pruning).

- **Key API (shape)**: `addLayer`, `connectLayers`, `bindInput`, `tick`, `tickImage` (when image I/O layers exist), `prune`, accessors (`getName`, `getLayers`, `getBus`).
- **Metrics output**: returns a `RegionMetrics` instance per tick.
- **Cross‑language notes**:
  - **Java**: canonical/“gold”; `RegionMetrics` is a separate class in `ai.nektron.grownet.metrics`.
  - **C++**: API shape mirrors Java; sometimes keeps an explicit `Tract` type (see **Tract**).
  - **Python/Mojo**: mirror Java semantics; naming follows the style rules you set.

**Layer**
 A set (usually homogeneous) of neurons considered at the same “depth.” Provides utilities to wire internally or between layers and to propagate activity through its neurons.

- **Key methods**: `forward(value)` (drive every neuron with a scalar), `endTick()` (end‑of‑step housekeeping), and sometimes `propagateFrom(...)` in shape‑aware layers (image I/O).
- **Instantiation**: created by `Region.addLayer(excitatoryCount, inhibitoryCount, modulatoryCount)` or as specialized I/O layers (see **InputLayer2D** / **OutputLayer2D**).

**Neuron**
 The fundamental processing element that receives inputs, chooses a **slot** (see **Slot**, **SlotEngine**), updates a **Weight** for that slot, and emits to its outgoing **Synapse** list when it “fires.”

- **Common state** (names vary by language):
  - `id` (string identifier)
  - `outgoing` (list of `Synapse` targets)
  - `slots` (map of **slot id** → **Weight**)
  - `lastInputValue`, `firedLast` (recent activity)
  - references to buses (see **LateralBus**) and slot configuration (see **SlotConfig**)
- **Fire path** (simplified): `onInput(value)` → choose or create slot → reinforce its Weight (modulated/inhibited by bus) → optionally “fire” → propagate to outgoing synapses.
- **Specializations**: `ExcitatoryNeuron`, `InhibitoryNeuron`, `ModulatoryNeuron`, `InputNeuron`, `OutputNeuron`.

**Synapse**
 A directed connection from one neuron to another. Holds linkage and may reference a per‑edge weight or simply route through the source neuron’s slot/weight updates (GrowNet’s “slotting” pushes most plasticity into the neuron’s slot table).

- **Flags**: may be tagged as `feedback` when created for backward/feedback paths.

**Weight**
 A compact record stored per **slot** inside a neuron. Tracks the effective strength and the threshold associated with that slot, plus bookkeeping for learning and pruning.

- **Typical fields/methods**: `getStrengthValue()`, `getThresholdValue()`, `reinforce(modulation)`, timestamps/counters used for “stale” detection.
- **Where it lives**: inside the neuron’s `slots` map.

**Tract**
 A logical conduit connecting a **source layer** to a **destination layer** (i.e., the inter‑layer edge set). Useful for bulk wiring, statistics, and potential future tract‑level pruning.

- **Cross‑language notes**:
  - **C++** often has an explicit `Tract` type returned or stored.
  - **Java** currently returns an **edge count** from `connectLayers` and keeps tract pruning as “future”; metrics still reflect synapse counts.
  - **Python/Mojo**: mirror Java unless you opt‑in to explicit Tract objects.

------

## Execution & learning

**Tick**
 One discrete simulation step for scalar input. The region:

1. Locates entry layers bound to a named **input port**,
2. Calls `forward(value)` on those layers,
3. Calls `endTick()` on all layers,
4. Aggregates **RegionMetrics** (events delivered, total slots, total synapses).

- **Output**: `RegionMetrics`.
- **Granularity**: You can break on neuron `onInput`, `select/create slot`, `reinforce`, `fire`, and synapse delivery to visualize propagation.

**Image Tick**
 A tick where the input is a 2D frame (e.g., grayscale image). The region finds input layers bound to the port and calls `forwardImage(frame)` on each **InputLayer2D**; then performs the same end‑of‑tick housekeeping and metrics aggregation.

- **Shape‑aware**: relies on **InputLayer2D** and optionally **OutputLayer2D** to map pixels to neurons.

**Reinforcement**
 Updating a **Weight** in response to activity, scaled by **modulation** and possibly dampened by **inhibition**. In GrowNet:

- Modulation (reward‑like) **increases** weight strength.
- Inhibition (suppress‑like) reduces effective updates or firing likelihood.
- Exact formulas are intentionally simple and local.

**Pruning**
 A maintenance pass that removes weak and/or stale synapses.

- **Inputs**: “stale window” (age/steps without activity) and “min strength.”
- **Output**: `PruneSummary` with `prunedSynapses` (and `prunedEdges` reserved for tract‑level work).
- **When**: usually invoked between training phases or at cadence.

------

## Slotting system

**Slot**
 An index into a neuron’s local **weight table** chosen as a function of the **current input** and the **recent input history**. Slots let a single neuron keep multiple “micro‑contexts” with separate thresholds/strengths.

- Stored in `slots: Map<int, Weight>` inside the neuron.

**SlotEngine**
 A small strategy object the neuron uses to:

- decide **which slot id** to use given `(lastInput, currentInput, knownSlots)`, and
- **select or create** the corresponding weight record.
   Implementations typically consider **percent delta** between current and last inputs.

**SlotConfig**
 Configuration for **SlotEngine**. Contains **policy** and policy parameters.

- **Typical policy enum**:
  - `FIXED`: always slot `0` (single‑slot neuron).
  - `NONUNIFORM`: pick from a fixed set of bins (e.g., based on percent delta bands).
  - `ADAPTIVE`: grow new slots on demand up to a `slotLimit`, then reuse nearest.
- **Cross‑language notes**: names/types map directly across Java/C++/Python/Mojo; exact thresholds/bins are kept coherent by the contract.

**Percent Delta (Δ%)**
 `abs(current - last) / max(abs(last), ε) * 100` used by `SlotEngine` to map to a bin (for NONUNIFORM) or to decide whether to spawn a new slot (for ADAPTIVE).

------

## Signaling & buses

**LateralBus**
 Per‑region (or per‑layer scope) bus that carries **modulation** and **inhibition** factors used during **reinforcement**. Neurons read these factors in `onInput(...)`.

- **Key methods**: `getModulationFactor()`, `getInhibitionFactor()`, and setters/pulses from `Region` (e.g., `pulseModulation`, `pulseInhibition` in some languages).

**RegionBus**
 A higher‑level bus reserved for batching or future cross‑layer coordination. Present to keep the API stable and to enable tract‑level features down the road.

**Modulation Pulse**
 A short‑lived increase to the bus’s modulation factor (reward‑like). Applied before a tick or periodically to bias strengthening.

**Inhibition Pulse**
 A short‑lived increase to the bus’s inhibition factor (suppress‑like). Useful to temper runaway excitation.

------

## I/O layers and helpers

**InputLayer2D**
 A shape‑aware input layer that exposes `forwardImage(frame)` (2D array) and internally distributes pixel values to **InputNeurons** laid out on a grid.

- **Parameters**: `gain` (scale inputs), `epsilonFire` (small base activity threshold).
- **Implements**: `forward(value)` (degenerate) and `endTick()`.

**OutputLayer2D**
 A shape‑aware output layer that aggregates/decays neuron outputs for a 2D layout.

- **Parameter**: `smoothing` (exponential decay of last emitted).
- **Exposure**: getters to read out the 2D field after ticks.

**InputNeuron / OutputNeuron**
 Specialized neurons sitting at the boundaries:

- **InputNeuron**: creates/uses slot `0`, sets threshold from the first observed values (with `epsilonFire`) and scales by `gain`.
- **OutputNeuron**: aggregates inputs and provides a smoothed “emitted” value for visualization.

**Ports**
 String names bound to sets of layer indices via `Region.bindInput(port, layers)` and `Region.bindOutput(...)`.

- Example: `bindInput("pixels", [inLayerIndex])` then call `tickImage("pixels", frame)`.

------

## Metrics, summaries & results

**RegionMetrics**
 Per‑tick totals that summarize what happened.

- **Fields** (logical shape):
  - `deliveredEvents` — count of entry‑layer activations (best‑effort; depends on how you count multi‑layer inputs),
  - `totalSlots` — sum of `slots.size()` across all neurons,
  - `totalSynapses` — total `outgoing.size()` across all neurons.
- **Java**: class moved to `ai.nektron.grownet.metrics`, fields are **private** with explicit getters, setters, and increment/add helpers (e.g., `incDeliveredEvents()`, `addSlots(long)`, `addSynapses(long)`).
- **C++/Python/Mojo**: mirror the Java behavior (provide mutators rather than writing fields directly).

**PruneSummary**
 Report returned by `Region.prune(...)`.

- **Fields**: `prunedSynapses`, `prunedEdges` (reserved for tract‑level).
- **When edges aren’t tracked** (e.g., Java today): `prunedEdges` remains `0`.

**Edge Count**
 An integer returned by `connectLayers(...)` denoting how many synapses were created during wiring.

------

## Wiring, growth & structure

**connectLayers(sourceIndex, destIndex, probability, feedback=false)**
 Randomly create synapses from every neuron in `source` to neurons in `dest` with the given probability.

- **`feedback`** flag marks the synapse for potential special handling.
- **Return**: **edge count** (Java/Python/Mojo) or a **Tract reference** (C++ variant).

**Random Wiring Probability**
 `[0.0, 1.0]`, clamped; values near `1.0` create dense connectivity; small values create sparse graphs.

**Feedback Edge**
 A synapse created with `feedback=true`. Reserved for future feedback‑specific learning/propagation rules.

**Slot Limit**
 Maximum number of slots a neuron can create (ADAPTIVE policy); `-1` or similar means unbounded within practical memory limits.

------

## Learning thresholds & activity

**Threshold Value**
 Per‑slot threshold derived from observed input magnitudes (e.g., initialized from first seen values for `InputNeuron`). Used to decide **firing** or to normalize reinforcement.

**Strength Value**
 Per‑slot weight magnitude that grows with reinforcement (modulation‑scaled) and decays implicitly through pruning/under‑use regimes.

**Fired Last / Last Input Value**
 Bookkeeping on the neuron’s most recent activity and input; used by **SlotEngine** and for debugging/breakpoints.

**Gain** (Input layers/neurons)
 Scale factor applied to inputs prior to slotting/threshold comparison.

**Epsilon Fire** (Input layers/neurons)
 A small fraction that sets a baseline threshold (prevents trivially firing on noise).

**Smoothing** (Output layers/neurons)
 Coefficient for exponential decay of last emitted value, giving a temporal trace.

------

## Execution vocabulary

**Activation / Fire**
 When a neuron updates a slot and decides to emit its output to outgoing synapses during a tick.

**Event**
 A single “delivery” into the network for that tick (e.g., one call to `forward(...)` per entry layer). The count is reflected in `RegionMetrics.deliveredEvents`.

**End‑of‑Tick Housekeeping**
 A per‑layer callback (`endTick()`) used to decay bus factors, apply smoothing, reset one‑tick flags, etc.

------

## Contract, style & cross‑language notes

**GrowNet Contract (YAML)**
 The master spec of class/method shapes, enums, and semantics. It keeps language ports coherent (Java/C++/Python/Mojo). When you extend the API (e.g., metrics move, new policies), update the YAML and realign all languages.

**Coding Style**

- **Names**: descriptive; avoid single‑letter locals in production paths.
- **Python/Mojo**: use snake_case for functions/methods/variables; **fields must not begin with `_`** (leading underscores reserved); module/file names reflect classes (`input_layer_2d.py`, `output_layer_2d.py`, one neuron class per file).
- **Java**: standard Java style; `RegionMetrics` is a separate class with private fields + accessors.
- **C++**: consistent smart‑pointer usage across containers; headers include what they use; `std::out_of_range` on index validation; keep `.h` vs `.cpp` responsibilities clean.

**Polarity Types**

- **ExcitatoryNeuron**: promotes downstream activation.
- **InhibitoryNeuron**: suppresses downstream activation or reduces reinforcement.
- **ModulatoryNeuron**: influences **modulation** (reward‑like factor) broadcast on the **LateralBus**.

**Image I/O flow**

- **Input**: `tickImage("pixels", frame)` (or equivalent), which calls `forwardImage(frame)` on bound input layers.
- **Output**: inspect **OutputLayer2D** smoothed emissions after `endTick()`.

------

## Benchmarking concepts

**End‑to‑End Latency**
 Wall‑clock time per tick from `Region.tick(...)` (or `tickImage`) entry to return. Compare across Java/C++/Python/Mojo.

**Micro‑benchmarks**
 Targeted timings for: slot selection, weight reinforcement, synapse fan‑out, prune pass. Helpful to diagnose hot spots (e.g., slot policy vs. container choices).

**Throughput**
 Ticks per second under a standard topology (fixed random seed; fixed wiring probability, same input stream).

------

## Debugging & observability

**Breakpoint Map**
 Recommended strategic breakpoints (especially in Java/Python) to follow a tick end‑to‑end:

1. `Region.tick` → just before calling entry layers.
2. `Layer.forward` → before iterating neurons.
3. `Neuron.onInput` → right at slot selection.
4. `Weight.reinforce` → before/after mutation.
5. `Neuron.fire` → just before iterating `outgoing` synapses.
6. `Layer.endTick` → to observe decay/reset.
7. `Region.tick` → before returning `RegionMetrics`.

**Metrics Counters**
 Use `RegionMetrics` mutator methods (`incDeliveredEvents`, `addSlots`, `addSynapses`) so you can set watchpoints and keep encapsulation intact (important in Java after the move to `ai.nektron.grownet.metrics`).

------

## Terminology quick list (A–Z)

- **Activation / Fire** — neuron emits to outgoing synapses during a tick.
- **ADAPTIVE / FIXED / NONUNIFORM** — `SlotPolicy` modes for slot selection/creation.
- **Bus (LateralBus / RegionBus)** — shared state for modulation/inhibition and coordination.
- **Delta Percent (Δ%)** — normalized change used to bin inputs to slots.
- **Edge** — synonym for synapse in wiring/connectLayers context.
- **Event** — one delivered activation into the network per entry layer per tick.
- **Feedback Edge** — synapse tagged as feedback.
- **Gain / Epsilon Fire** — input scale and baseline fire threshold.
- **Image Tick** — a tick driven by a 2D frame, using shape‑aware layers.
- **Inhibition / Modulation** — factors that suppress or encourage reinforcement/firing.
- **InputLayer2D / OutputLayer2D** — 2D I/O layers for image‑like data.
- **InputNeuron / OutputNeuron** — boundary neurons handling I/O specifics.
- **Layer** — collection of neurons at the same stage.
- **Neuron** — fundamental processing unit; owns **slots** and **outgoing** synapses.
- **Outgoing** — a neuron’s list of outgoing synapses.
- **Port** — string binding name for input (and future output) groups of layers.
- **Prune / PruneSummary** — remove weak/stale synapses; returns counts.
- **Random Wiring Probability** — chance to create a synapse during wiring.
- **Reinforcement** — weight update with modulation/inhibition scaling.
- **Region** — top‑level orchestrator of layers, tick, wiring, prune.
- **RegionMetrics** — per‑tick counters (deliveredEvents, totalSlots, totalSynapses).
- **Slot** — per‑neuron “bin” entry storing a **Weight**.
- **SlotConfig / SlotEngine** — policy + logic for selecting/creating slots.
- **Slot Limit** — cap on how many slots a neuron can keep (ADAPTIVE).
- **Synapse** — directed connection between neurons.
- **Tick** — one simulation step for scalar input; image tick for 2D.
- **Tract** — logical inter‑layer connector (explicit in some languages).
- **Weight** — per‑slot strength/threshold and learning/bookkeeping.

