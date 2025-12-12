# GrowNet — Unified Event‑Driven Architecture (Design Spec v2)

**Status:** active draft (v2) · **Audience:** software engineers & data scientists · **Reference implementations:** Python, Java, C++, Mojo  
**This document supersedes** the earlier “GrowNet: Theory of Change” design note. See v1 here for historical context. fileciteturn6file0

---

## 1. Naming & Philosophy

- **Project / model:** **GrowNet**  
- **Core idea:** an **online, slot‑gated, event‑driven** network that can **grow** capacity and **learn locally** (no global error/backprop).  
- **Design rules:**
  1) **Consistency first** — every neuron exposes **two methods**: `onInput(value, …) -> fired` and `onOutput(amplitude)`.  
  2) **Slots (per‑neuron)** capture stimulus regimes; thresholds adapt **locally** (T0 imprint + T2 homeostasis).  
  3) **Buses, not backprop** — inhibition and neuromodulation are broadcast via a lateral bus.  
  4) **Simplicity over imitation** — biologically inspired, not biologically identical. When unsure, pick the simpler engineering primitive.

---

## 2. Architectural Overview

```
  +----------------------- Region ------------------------+
  |                                                       |
  |  Input ports -> [InputLayer2D] -> Hidden [E/I/M] -> [OutputLayer2D] -> Output frame
  |                      |                 |                   |
  |                LateralBus         LateralBus           LateralBus
  |                                                       |
  |  Phase A: inject → onInput/Output → local routing     |
  |  Phase B: flush tracts once to destination layers     |
  |  Finalize: OutputLayer2D.end_tick() → EMA frame       |
  |  Housekeep: decay buses, prune/grow, metrics          |
  +-------------------------------------------------------+
```

- **Layers:** Container of neurons + adjacency (intra‑layer routing) + **LateralBus** (inhibition/modulation).  
- **Region:** Owns layers, inter‑layer **tracts**, input ports, and the **two‑phase tick**.

---

## 3. Data Structures (language‑agnostic)

### 3.1 Slot (`Weight`)
A slot is an independent thresholding unit inside a neuron.
- **Fields**
  - `strength_value: float` — synaptic efficacy (updated via `reinforce` with smooth clamp).  
  - `threshold_value: float` — adaptive threshold.  
  - `first_seen: bool` — whether T0 imprint was applied.  
  - `ema_rate: float` — firing EMA (for T2).  
  - `hit_count: int` — exposure counter; saturates (e.g., 10,000) to freeze strength.  
- **Methods**
  - `reinforce(modulation, inhibition)` — multiplicative updates, non‑linear, bounded.  
  - `update_threshold(input_value) -> fired: bool` — T0 + T2 hybrid (see §4).

> Slots are **open‑bounded** by default (the neuron may create new ones); a global cap can be added later for resource budgets.

### 3.2 Synapse
A **connection object** responsible for **routing** an event from source neuron/slot to a destination neuron index. It may reference the source slot’s `Weight` (shared view) or cache a projection gain. Synapse carries metadata (age, usage) for **pruning**.

### 3.3 Neuron (base)
- **Fields**
  - `slots: map[int, Weight]` — slot id → weight.  
  - `fired_last: bool`, `last_input_value: float`.  
  - `bus: LateralBus` (layer‑scoped view).  
- **Methods**
  - `onInput(value, [bus/mod, inh]) -> bool` — apply gating at slots, update local state, return fired.  
  - `onOutput(amplitude)` — **called only if fired**; default no‑op (hidden/input), **accumulation** for outputs.  
  - `fire(amplitude)` — (internal) notifies tracts / layer for propagation; **outputs never call this**.

### 3.4 Neuron phenotypes
- **ExcitatoryNeuron** — default relay: if fired, layer propagation proceeds.  
- **InhibitoryNeuron** — emits **inhibition** into its layer bus (e.g., sets `inhibition_factor < 1` for ΔT ticks).  
- **ModulatoryNeuron** — emits **modulation** (e.g., sets `modulation_factor > 1` temporarily).  
- **InputNeuron** — **single-slot** sensor; uses S0 imprint; may `fire` (so upstream routing works).  
- **OutputNeuron** — **single-slot** actuator; `onInput` gates & reinforces; `onOutput` accumulates; **never fires**.

### 3.5 LateralBus
```text
inhibition_factor: float  # <= 1.0, decays to 1.0
modulation_factor: float  # default 1.0, decays to 1.0
decay()                   # called each tick
```

### 3.6 Layer
- Holds `neurons`, `adjacency` (intra‑layer synapses), `bus`.  
- **Tick contract (within a layer):** for each neuron input in Phase A:  
  1) `fired = neuron.onInput(value, context)`  
  2) if `fired`: `neuron.onOutput(value)` then **propagate** to neighbors.

### 3.7 Region
- Holds layers, inter‑layer **tracts**, and **input port bindings**.  
- Provides **convenience factories** (e.g., `add_input_layer_2d(...)`, `add_output_layer_2d(...)`).  
- **tick_image(port, image)**: inject to all bound input layers, **flush** tracts (Phase B), finalize outputs, decay buses, return metrics.

---

## 4. Learning & Thresholds

### 4.1 Non‑linear reinforcement (bounded)
- Strength updates are non‑linear, ceiling‑bounded, and **saturate** as `hit_count → saturation_limit` (e.g., 10,000).  
- Inhibition and modulation **scale** the effective step each time.

### 4.2 Adaptive thresholds (T0 + T2 hybrid)
- **T0 imprint:** on first effective stimulus `s0`, set `threshold_value ≈ s0 * (1 - epsilon_fire)`; guarantees the *same* pattern fires next time.  
- **T2 homeostasis:** each tick, with `fired ∈ {0,1}`:
  - `ema_rate = (1 - beta) * ema_rate + beta * fired`  
  - `threshold_value += eta * (ema_rate - r_star)`  
- **Default knobs:** `beta = 0.01`, `eta = 0.02`, `r_star = 0.05`, `epsilon_fire = 0.01`, T0 slack = `0.02`.  
- Behavior: if a slot fires **too often**, θ rises; if **too rarely**, θ falls, keeping a target **spike rate**.

---

## 5. Growth, Pruning & Feedback

### 5.1 Slot growth (per neuron)
- **Trigger:** new input lies **outside** the covered slot regimes (e.g., %‑delta bucket unseen or distance margin exceeded).  
- **Action:** allocate a new slot with T0 imprint; initialize with low strength.

### 5.2 Synapse/neuron growth (layer)
- **Trigger candidates:** persistent routing bottlenecks, high Fisher‑style importance, or accumulated error proxy (domain‑specific).  
- **Action:** add synapses to high‑utility neighbors; optionally add neurons (configurable budget).

### 5.3 Pruning
- **LRU + low strength:** prune synapses unused for **K** ticks or whose `strength_value < ε`.  
- **Never prune** input/output neurons automatically; gate via layer config.  
- Keep hysteresis to prevent oscillation.

### 5.4 Feedback loops
- **Positive feedback:** allow **explicit** feedback tracts but cap gain and hop count.  
- **Negative feedback:** leverage **InhibitoryNeuron** populations to dampen runaway activity.

---

## 6. I/O Layers for Images

### 6.1 InputLayer2D
- Shape‑aware (height×width).  
- Each pixel → **InputNeuron** (single slot).  
- `forward_image(image)`: for each pixel → `onInput`; if fired → `onOutput` (no‑op).

### 6.2 OutputLayer2D
- Shape‑aware output buffer.  
- `propagate_from(i, value)`: `onInput` then `onOutput` → accumulate.  
- `end_tick()`: write per‑neuron EMA into the output **frame** matrix.

---

## 7. Two‑Phase Tick

1) **Phase A – Inject & local routing**  
   - Region injects input (e.g., `tick_image(port, image)`).  
   - Each layer processes: `onInput` → (if fired) `onOutput` → intra‑layer propagate.  
2) **Phase B – Tract flush**  
   - Region flushes **inter‑layer** tracts once. Output layers then call `end_tick()`.  
3) **Housekeeping**  
   - Buses decay, pruning/growth run if scheduled, metrics aggregated.

**Invariant:** **Output neurons never call `fire`**; they are sinks/actuators.

---

## 8. Cross‑Language API Parity

| Concept        | Python                              | Java                                              | C++                                                | Mojo                                   |
|----------------|-------------------------------------|---------------------------------------------------|----------------------------------------------------|----------------------------------------|
| Base hook      | `def onOutput(self, amplitude)`     | `public void onOutput(double amplitude)`          | `virtual void onOutput(double amplitude)`          | `fn onOutput(self, amplitude: Float64)`|
| Input neuron   | reads `self.bus`                    | `onInput(value, modulation, inhibition)`          | `onInput(value, const LateralBus&)`                | `onInput(value, modulation, inhibition)` (optional args) |
| Output neuron  | `end_tick()` writes frame via layer | `endTick()`                                       | `endTick()`                                        | `end_tick()`                            |
| Image I/O tick | `region.tick_image(port, image)`    | `region.tickImage(port, image)`                   | `region.tickImage(port, image)`                    | `region.tick_image(port, image)`        |

> Minor signature differences exist (e.g., bus passed as params vs. captured). Behavior is identical across languages.

---

## 9. Defaults & Tuning

- **Threshold/homeostasis:** `beta=0.01`, `eta=0.02`, `r_star=0.05`.  
- **Inhibition / modulation:** start with mild values (e.g., inhibition_factor 0.8 for 1–2 ticks; modulation_factor 1.2).  
- **Saturation:** `hit_count_limit = 10_000`.  
- **Pruning:** start conservative (e.g., no prune first runs), then enable LRU ≥ 500 ticks inactivity + `strength_value < 0.02`.

---

## 10. Instrumentation & Visualization

- **Per‑tick metrics:** delivered events, total slots, total synapses, output nonzeros, mean output.  
- **Per‑neuron peek:** `neuron_value(mode)` helper (slots, θ, strength, ema_rate, last_input, fired_last).  
- **Visualizer hooks:** stream **fire events**, **slot updates** (θ, strength) and **bus levels**; keep API stable so UI can be shared across languages.

---

## 11. Files & Demos (reference names)

- **Python:** `input_neuron.py`, `output_neuron.py`, `input_layer_2d.py`, `output_layer_2d.py`, `image_io_demo.py`  
- **Java:** `InputNeuron.java`, `OutputNeuron.java`, `InputLayer2D.java`, `OutputLayer2D.java`, `ImageIODemo.java`  
- **C++:** `InputNeuron.h`, `OutputNeuron.h`, `InputLayer2D.h`, `OutputLayer2D.h`, `ImageIODemo.cpp`  
- **Mojo:** `input_neuron.mojo`, `output_neuron.mojo`, `input_layer_2d.mojo`, `output_layer_2d.mojo`, `image_io_demo.mojo`

---

## 12. Open Questions

- **Slot creation policy:** exact distance test / %‑delta bucket mapping for non‑image domains.  
- **Growth cadence:** per‑tick vs. periodic audit (every N ticks) to avoid jitter.  
- **Cross‑region modulation:** global neuromodulator broadcasts across regions (later).

---

## 13. Roadmap (updated)

- **R1**: lock API surface (this doc) and run the three demos (Py/Java/C++).  
- **R2**: add pruning policy behind a feature flag; measure effect on stability.  
- **R3**: enable slot growth with a simple %‑bucket trigger; add logs for each allocation.  
- **R4**: start visualization MVP (event stream → browser canvas/SVG).  
- **R5**: domain dataset micro‑benchmarks (Omniglot slice; then finance series).

---

### Appendix A — T0/T2 Reference Snippet (pseudo)

```text
if not slot.first_seen:
    slot.threshold_value = effective * (1.0 - epsilon_fire)
    slot.first_seen = true

fired = (effective > slot.threshold_value)

slot.ema_rate = (1 - beta) * slot.ema_rate + beta * (1.0 if fired else 0.0)
slot.threshold_value += eta * (slot.ema_rate - r_star)
```

### Appendix B — EMA frame at output

```text
if accumulated_count > 0:
    mean = accumulated_sum / accumulated_count
    output_value = (1 - smoothing) * output_value + smoothing * mean
accumulated_sum = 0
accumulated_count = 0
```