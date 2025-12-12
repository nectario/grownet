Absolutely—here’s a **thorough GrowNet glossary** you can lift straight into your next thread. I grouped terms by theme, gave crisp definitions, and (where helpful) showed **cross‑language name parity**: **Java / C++ / Python / Mojo**. The glossary reflects the latest v3 design (Java = gold), C++ and Python aligned, and Mojo kept close to Python with explicit types and `fn` syntax.

------

# GrowNet Glossary (v3)

## A. Core structural concepts

### **Region**

- **What it is:** The top‑level container of computation. Owns layers, input/output port bindings, region‑level buses, random wiring helpers, and tick/prune orchestration.
- **Responsibilities:**
  - Create layers (mixed, input 2D, output 2D).
  - Bind external inputs to layers via **ports**.
  - Advance time via **tick** (scalar) and **tickImage**/**tick_image** (2D frames).
  - Maintain region‑level **metrics** and perform **pruning**.
- **Key methods (shape):**
   `addLayer / add_layer`, `addInputLayer2D / add_input_layer_2d`, `addOutputLayer2D / add_output_layer_2d`,
   `connectLayers / connect_layers`, `bindInput / bind_input`, `bindOutput / bind_output`,
   `tick`, `tickImage / tick_image`, `prune`, accessors (`getName / get_name`, `getLayers / get_layers`, `getBus / get_bus`).
- **Cross‑language names:**
   Java/C++: camelCase; Python/Mojo: `snake_case` for functions & methods; **fields do not start with `_`**.

------

### **Layer**

- **What it is:** An ordered collection of neurons. A **mixed layer** can hold excitatory, inhibitory, and modulatory neurons. Specializations exist for 2D I/O.
- **Responsibilities:** Housekeeping per tick (`forward`, `endTick / end_tick`), managing the neuron list, providing iteration and wiring targets.
- **Common ops:** `getNeurons / get_neurons`, `forward`, `endTick / end_tick`.

------

### **Neuron**

- **What it is:** The basic unit that receives inputs, maps them to **slots**, updates a selected **weight**, determines **firing**, and propagates signals to its outgoing **synapses**.
- **State (typical):**
  - Identity: `id` or `name`.
  - I/O history: `last_input_value`, `fired_last`, `have_last_input` flags.
  - Slot map: `slots` (`slot_id -> Weight`).
  - Outgoing synapses collection.
  - References to buses (e.g., `LateralBus`) and **SlotEngine**.
- **Lifecycle (per input):**
  1. Choose a slot via **SlotEngine** (possibly create on demand).
  2. Update/strengthen the slot’s **Weight** (modulation/inhibition aware).
  3. Decide to **fire** (threshold/strength logic).
  4. If fired, **emit** to outgoing synapses.
- **Specializations:** `ExcitatoryNeuron`, `InhibitoryNeuron`, `ModulatoryNeuron`, `InputNeuron`, `OutputNeuron`.

------

### **Synapse**

- **What it is:** A directed edge from a presynaptic neuron to a postsynaptic neuron, carrying a signal when the source fires.
- **Attributes:** Reference to target neuron, a **Weight** (or uses the source neuron’s slot weight as the emitted value), and a `feedback` flag for back‑edges.
- **Common ops:** `transmit(value)` or inlined propagation in the neuron's fire path.

------

### **Weight**

- **What it is:** The learnable scalar associated with a **slot**. Encodes (minimally) **strength**, **threshold**, and bookkeeping (e.g., last update / staleness).
- **Common ops:** `reinforce(modulation_factor)`, `decay()`, getters/setters for strength and threshold.

------

### **Slot**

- **What it is:** A discrete bin keyed by **slot_id** that represents a local “context” or regime of the input space (e.g., magnitude band or percent‑delta band).
- **Role:** Inputs do not directly update a single monolithic weight; they are routed to a bin (slot), which then learns separately.

------

### **SlotEngine**

- **What it is:** The selection/creation policy for slot IDs given the current input (and optionally last input).
- **Capabilities:**
  - `slot_id(last_input, current_input, known_slots)` → `int`
  - `select_or_create_slot(neuron, input_value)` → `Weight&/Weight`
  - `compute_bin_for_percent_delta(delta_percent, nonuniform_map)` → `int` (where applicable)
- **Policies (via `SlotConfig.policy`):**
  - **FIXED**: fixed number of uniform bins.
  - **NONUNIFORM**: explicit, non‑uniform partition (e.g., hand‑set delta bands).
  - **ADAPTIVE**: grows slots on demand based on observed input regimes.

------

### **SlotConfig**

- **What it is:** Configuration passed to neurons/SlotEngine specifying policy, fixed bin count, non‑uniform partition map, thresholds, and limits.
- **Typical fields:** `policy`, `fixed_bins`, `nonuniform_bins (map<int,Weight>)`, `slot_limit`.

------

## B. Buses & signaling

### **LateralBus**

- **What it is:** A per‑region (or shared) carrier for global **modulation** and **inhibition** factors used during learning/firing.
- **Common ops:** `get_modulation_factor`, `get_inhibition_factor`, `pulse_modulation(factor)`, `pulse_inhibition(factor)`, exponential decays at `end_tick`.

------

### **RegionBus**

- **What it is:** Reserved for region‑level batching or inter‑layer signaling (tract aggregation). Often a façade or placeholder for future expansion.

------

## C. Connectivity & topology

### **Tract**

- **What it is:** A convenience object that represents a (possibly probabilistic) **connection pattern** between two layers.
- **Construction:** `connect_layers(source_index, dest_index, probability, feedback=false)`
- **Runtime role:** Optionally registers **fire hooks** on source neurons to deliver events to destination neurons (depending on implementation); today most regions connect by directly creating synapses in the wiring pass.

------

### **Feedback edge (synapse)**

- **Definition:** A connection marked as feedback (e.g., for top‑down influence). Set by `feedback=true` in `connect_layers`.

------

### **Port / Input Port / Output Port**

- **What it is:** A named binding that links the outside world to one or more entry (or exit) layers.
- **Use:** `bind_input("port_name", [layer_indices])`, `bind_output("port_name", [layer_indices])`.

------

## D. Execution model (time & flow)

### **Tick (scalar tick)**

- **What it is:** One **time step** in which a scalar input value is fed into all layers bound to a named port.
- **Sequence (Region):**
  1. Look up port → entry layers.
  2. For each entry layer: `forward(value)`.
  3. For every layer: `endTick / end_tick` (decays buses, clears ephemeral flags).
  4. Aggregate **RegionMetrics** (slots & synapses counts, delivered events).

------

### **Image Tick**

- **What it is:** A tick carrying a 2D numeric frame (e.g., grayscale image).
- **Sequence:** Same as scalar tick, but entry layers must be `InputLayer2D`, and the call is `forwardImage(frame)` / `forward_image(frame)`.

------

### **Forward (layer)**

- **What it is:** Drive all neurons in the layer with the provided input (scalar or per‑pixel mapping in 2D).
- **Common ops:** For Input/Output 2D, helpers compute per‑neuron pixel index and emit or collect.

------

### **End‑of‑tick (layer)**

- **What it is:** Housekeeping pass (e.g., bus decay, output decay smoothing, clearing flags).

------

## E. Learning & dynamics

### **Reinforce**

- **What it is:** Increase the weight strength based on the current modulation factor. In some implementations, inhibition reduces effective firing probability or strength.
- **Typical signature:** `reinforce(modulation_factor)`.

------

### **Threshold**

- **What it is:** The minimum level required for a slot to count as “fired” for the neuron (variously used as emission or gating threshold). Often initialized on first observation (“first seen”) and updated by policy.

------

### **Decay**

- **What it is:** Exponential decrease applied to bus signals (modulation/inhibition) and (optionally) output emissions (e.g., output neuron’s `lastEmitted`).

------

## F. 2D I/O specializations

### **InputLayer2D**

- **What it is:** A layer whose neurons correspond to a 2D lattice (height × width).
- **Construction:** `InputLayer2D(height, width, gain, epsilonFire)`
- **Forward path:** `forwardImage / forward_image` maps each pixel to the corresponding input neuron.

------

### **InputNeuron**

- **What it is:** A neuron specialized for ingesting external input; often keeps a **gain** parameter and **epsilonFire** (epsilon margin to trigger initial threshold).
- **Behavior:** On the first observation, initializes slot threshold; then reinforces and possibly fires.

------

### **OutputLayer2D**

- **What it is:** A layer whose neurons collect signals to form an output frame; often has **smoothing** decay to simulate persistence.
- **Forward path:** Typically receives via synapses; its `end_tick` applies smoothing.

------

### **OutputNeuron**

- **What it is:** A neuron specialized to emit (and store) an output value per pixel; keeps `last_emitted` and `smoothing`.

------

## G. Metrics, pruning, and maintenance

### **RegionMetrics**

- **What it is:** Lightweight counts produced every tick for visibility & benchmarking.
- **Canonical fields:**
  - `delivered_events` — number of input deliveries made this tick (per entry layer activation).
  - `total_slots` — sum of slots across all neurons at the end of the tick.
  - `total_synapses` — count of outgoing synapses across all neurons.
- **API style:** Prefer private fields with **getters**, **setters/adders**, and **increment** helpers (`incDeliveredEvents()`, `addSlots(n)`, `addSynapses(n)` in Java/C++; analogous snake_case methods in Python/Mojo).

------

### **Prune / Pruning**

- **What it is:** Maintenance pass to remove **stale** (not updated for N ticks) or **weak** (strength < threshold) synapses; tract pruning is reserved for future.
- **Parameters:** Synapse stale window, minimum strength; (tract window/strength reserved for future).
- **Output:** **PruneSummary**.

------

### **PruneSummary**

- **Fields:**
   `pruned_synapses` — count of removed synapses;
   `pruned_edges` — reserved for tract/edge removal when enabled.

------

## H. Configuration & contracts

### **GrowNet Contract (YAML)**

- **What it is:** The master, language‑agnostic **API & behavior contract**. Captures constructor shapes, method signatures, policies, and naming conventions across languages.
- **Purpose:** Keeps Java, C++, Python, and Mojo in lock‑step.

------

### **SlotPolicy**

- **Values:** `FIXED`, `NONUNIFORM`, `ADAPTIVE`. Controls slot selection strategy in **SlotEngine**.

------

### **Random wiring probability**

- **What it is:** Probability used by `connect_layers` that any given pair (source neuron, destination neuron) is connected.
- **Range:** `[0.0, 1.0]`, clamped at the call site.

------

## I. Debugging & instrumentation

### **Fire hook**

- **What it is:** A callback registered on neurons in some implementations (e.g., inside `Tract`) so that when a source neuron fires, the tract can intercept and route the event. Useful for tracing and breakpoints.

------

### **Breakpoint waypoints**

- **Recommended sites:** `Region.tick / tick_image`, `Layer.forward`, `Neuron.on_input`, `SlotEngine.select_or_create_slot`, `Weight.reinforce`, `Neuron.fire`, `Synapse.transmit`, `Layer.end_tick`, `Region.prune`.

------

## J. Benchmarking

### **Latency (end‑to‑end)**

- **Definition:** Time from input delivery at `tick` to completion of `end_tick` and metrics aggregation.
- **Mode:** Scalar and image ticks.

------

### **Micro‑benchmarks**

- **Examples:**
   slot selection cost, reinforce cost, synapse traversal cost, per‑pixel forward cost, prune pass cost, memory churn across N ticks.

------

## K. Coding style (cross‑language)

- **Java:** Idiomatic Java (camelCase), POJO‑style metrics (private fields + getters/setters), explicit types.
- **C++17:** CamelCase methods to match Java surface shape; owning containers use `std::vector<std::shared_ptr<Neuron>>` for layers; favor explicit includes and `std::` qualifiers.
- **Python:** `snake_case` for functions/methods; **no leading underscore for fields**; one class per file (e.g., `input_neuron.py`, `output_neuron.py`), and `input_layer_2d.py`, `output_layer_2d.py`.
- **Mojo:** Mirrors Python names, uses `fn` with explicit parameter/return types, avoids evolving/exotic features, uses `mut` instead of inout patterns.

------

## L. Frequently confused pairs

- **LateralBus vs RegionBus:** LateralBus carries modulation/inhibition and decays each tick; RegionBus is a region‑scope conduit/placeholder for tract batching and future features.
- **Weight vs Synapse:** Weight is the learnable scalar (per slot); Synapse is the directed edge that carries signals to a target neuron.
- **Slot vs Bin:** In practice synonyms; “slot” is the project term.
- **Feedback edge vs Feedforward edge:** Same data structure; feedback flagged to indicate reverse/top‑down pathway.
- **Tick vs Image Tick:** Scalar vs 2D frame path; both end with `end_tick` and metric aggregation.

------

## M. Canonical region API (shape recap)

- `Region(name)`
- `addLayer(e_count, i_count, m_count)` / `add_layer(...)`
- `connectLayers(src_idx, dst_idx, probability, feedback=false)` / `connect_layers(...)`
- `bindInput(port, [layer_indices])` / `bind_input(...)`
- `bindOutput(port, [layer_indices])` / `bind_output(...)`
- `pulseInhibition(f)` / `pulseModulation(f)` (via bus)
- `tick(port, value)`
- `tickImage(port, frame2d)` / `tick_image(port, frame2d)`
- `prune(synapse_stale_window, synapse_min_strength)` → `PruneSummary`
- Accessors: `getName/getLayers/getTracts(getTracts if present)/getBus`
- `RegionMetrics { delivered_events, total_slots, total_synapses }`
- `PruneSummary { pruned_synapses, pruned_edges }`

------

### Quick note on files

Some older uploads in this thread appear to have expired on my side. That doesn’t affect this glossary, but if you want me to cross‑check any specific definitions **against the latest code**, just re‑upload the archives in the new thread and I’ll verify line‑by‑line.

------

If you want, I can also generate a **one‑page printable PDF** version of this glossary for your NeurIPS prep, or fold it into the “Concepts” section of the design spec v3.