
---

# GrowNet — A Practical Tutorial (for Engineers & Data Scientists)

**Goal:** understand and run GrowNet without needing a neuroscience background.
You’ll build a tiny network, watch it learn online, wire layers into a region, and see growth/pruning signals.

---

## Contents

* [What is GrowNet (1 minute)](#what-is-grownet-1-minute)
* [Glossary (plain language)](#glossary-plain-language)
* [Install & run](#install--run)
* [How a neuron works](#how-a-neuron-works)
* [Hello, Layer](#hello-layer)
* [Slots sanity check](#slots-sanity-check)
* [Regions, tracts, and the two‑phase tick](#regions-tracts-and-the-two-phase-tick)
* [Inhibition & modulation (one‑tick control)](#inhibition--modulation-one-tick-control)
* [Pruning](#pruning)
* [One number per neuron (logging)](#one-number-per-neuron-logging)
* [Tuning the 4 scalars](#tuning-the-4-scalars)
* [Small experiments](#small-experiments)
* [FAQ](#faq)
* [Appendix A — Region API (reference impl)](#appendix-a--region-api-reference-impl)
* [Appendix B — Region demo](#appendix-b--region-demo)

---

## What is GrowNet (1 minute)

* **Event‑driven network.** A neuron **fires** when one of its **slots** (sub‑units) becomes strong enough to cross its own threshold.
* **Local learning, no backprop.** Each slot keeps tiny state and updates it on the spot; thresholds self‑calibrate to a target firing rate.
* **Dynamic structure.** New slots or connections appear when the stream presents unfamiliar changes; stale & weak connections are pruned.
* **Three levels:** **Neuron** → **Layer** (pool with a local bus) → **Region** (group of layers + inter‑layer tracts, with a two‑phase tick).

> Analogy: a **neuron is a freeway interchange**, **slots are its toll lanes**, **synapses are exit ramps**, a **layer** is a city district, and a **region** is the whole metro area.

---

## Glossary (plain language)

* **Slot** – a small sub‑unit inside a neuron. Different slots specialize to different **percent changes** of the input. State:

  * `strength_value` (how “open” the gate is)
  * `threshold_value` (gate height)
  * `ema_rate` (recent firing rate)
* **Neuron** – a container of slots. If the active slot crosses its threshold, the neuron **fires**.
* **Synapse** – a directed connection to another neuron with its **own** weight+threshold (so routing learns independently).
* **LateralBus** – one‑tick signals (inhibition & learning‑rate modulation) **within a layer**.
* **RegionBus** – same idea, but **across all layers** in a region.
* **Layer** – a pool of neurons (excitatory, inhibitory, modulatory).
* **Region** – several layers plus **tracts** (bundles of cross‑layer synapses) and a two‑phase scheduler.

**Four scalars (rarely tuned):**

* `EPS` (T0 slack) – buffer for the first threshold. Default **0.02**.
* `BETA` (EMA horizon) – how fast recent firing is remembered. Default **0.01**.
* `ETA` (adapt speed) – how fast thresholds chase the target rate. Default **0.02**.
* `R_STAR` (target rate) – desired average firing rate. Default **0.05**.

---

## Install & run

From the repo root:

```bash
# 1) Python environment (3.12+ or your 3.14 build)
python -m venv .venv
# Windows: .venv\Scripts\activate
# Linux/macOS:
source .venv/bin/activate

pip install --upgrade pip
pip install numpy tqdm pillow   # pillow only if you use omniglot_numpy.py

# 2) Sanity check: run the region demo (see Appendix B)
python src/python/region_demo.py
```

> **Tip:** Make sure Python filenames match imports in case‑sensitive environments (Linux). Use lowercase file names like `weight.py`, `neuron.py`, `layer.py`, `region.py`.

---

## How a neuron works

**Flow:**

1. Choose a **slot** based on percent change vs. the last input (0–10%, 10–20%, …).
2. **Reinforce** the slot (non‑linear, capped).
3. **Update threshold:**

   * **T0 imprint:** on first input, `threshold_value = |x| * (1 + EPS)`.
   * **T2 homeostasis:** nudge threshold toward `R_STAR` using `EMA`.
4. If `strength_value > threshold_value`, the neuron **fires**.

**Pseudocode:**

```python
def on_input(self, value: float):
    slot = self.select_slot(value)                         # choose by percent change
    slot.reinforce(self.bus.modulation_factor,
                   self.bus.inhibition_factor)
    if slot.update_threshold(value):                       # T0 + T2
        self.fire(value)                                   # propagate
```

---

## Hello, Layer

```python
from layer import Layer
import random

layer = Layer(excitatory_count=20, inhibitory_count=5, modulatory_count=3)

for step_index in range(1_000):
    layer.forward(random.random())
    if step_index % 200 == 0:
        readiness_values = [n.neuron_value("readiness") for n in layer.neurons]
        print(f"[step {step_index}] avg readiness={sum(readiness_values)/len(readiness_values):.3f}")
```

What to expect: readiness grows as slots specialize; inhibitory/modulatory neurons occasionally nudge learning for one tick.

---

## Slots sanity check

```python
from layer import Layer

layer = Layer(excitatory_count=1, inhibitory_count=0, modulatory_count=0)
neuron = layer.neurons[0]

for input_value in [10.0, 11.0, 11.2, 13.0, 13.1]:
    neuron.on_input(input_value)

print("slot ids:", sorted(neuron.slots.keys()))
# IDs correspond to ~10% bins: 0, 10, 20, 30, ...
```

---

## Regions, tracts, and the two‑phase tick

A **Region** holds layers and **Tracts** (bundles of connections between layers).
We use a **two‑phase tick** for stability:

1. **Phase A** – deliver external input to entry layers; intra‑layer propagation happens immediately.
2. **Phase B** – flush inter‑layer queues once (Tracts deliver cross‑layer events).
3. **Decay** – buses reset their one‑tick signals.

```python
from region import Region
import random

region = Region("vision")
layer_in  = region.add_layer(40, 8, 4)
layer_out = region.add_layer(30, 6, 3)

region.bind_input("pixels", [layer_in])
region.connect_layers(layer_in, layer_out, probability=0.10, feedback=False)
region.connect_layers(layer_out, layer_in, probability=0.01, feedback=True)  # sparse feedback

for step_index in range(2_000):
    metrics = region.tick("pixels", random.random())
    if (step_index + 1) % 200 == 0:
        print(f"[{step_index+1}] delivered={metrics['delivered_events']:.0f} "
              f"slots={metrics['total_slots']:.0f} syn={metrics['total_synapses']:.0f}")
```

---

## Inhibition & modulation (one‑tick control)

* **Inhibitory neurons** set `bus.inhibition_factor` (e.g., 0.7) for the current tick.
* **Modulatory neurons** set `bus.modulation_factor` (e.g., 1.5) for the current tick.
* Region‑wide pulses:

```python
region.pulse_inhibition(0.5)   # calm the region this tick
region.pulse_modulation(2.0)   # learn faster this tick
```

Both reset during `decay()`.

---

## Pruning

We prune **per‑neuron synapses** and **tract edges** that are **stale** and **weak**:

```python
summary = region.prune(
    synapse_stale_window=10_000, synapse_min_strength=0.05,
    tract_stale_window=10_000,   tract_min_strength=0.05
)
print(summary)  # {'pruned_synapses': ..., 'pruned_edges': ...}
```

---

## One number per neuron (logging)

A neuron doesn’t have a single “value,” so we provide summaries (already in `neuron.py`):

* `"readiness"` – `max(strength - threshold)` across slots
* `"firing_rate"` – mean of `ema_rate` across slots
* `"memory"` – sum of `abs(strength)` across slots

```python
value = neuron.neuron_value("readiness")
```

---

## Tuning the 4 scalars

* **`EPS`** bigger → less sensitive on the first input (start 0.02).
* **`BETA`** bigger → recent firing weighs more (start 0.01).
* **`ETA`** bigger → thresholds move faster (start 0.02).
* **`R_STAR`** bigger → neurons aim to fire more often (start 0.05).

Prefer adjusting **layer sizes** and **wiring probabilities** first.

---

## Small experiments

1. **Slot‑creation surge** – feed alternating values (e.g., 0.1 / 0.9) and watch new slot IDs appear.
2. **Inhibition pulse** – every 100 ticks, call `region.pulse_inhibition(0.5)` and log readiness/memory.
3. **Pruning** – over‑wire tracts, run for a while, then call `region.prune()` and count removals.
4. **Two regions** – “vision” feeding “motor”; log delivered events across the tract.

---

![GrowNet Overview](C:\Development\Projects\GrowNet\docs\images\grownet_overview.png)

## FAQ

**Q: What decides which slot is used?**
A: The **percent change** vs. the last input for that neuron, binned in \~10% steps.

**Q: What is a neuron’s value?**
A: Use `neuron_value("readiness" | "firing_rate" | "memory")` for a one‑number summary.

**Q: How do you keep feedback from exploding?**
A: The **two‑phase** region tick queues cross‑layer traffic and flushes once per tick.

**Q: How close is this to biology?**
A: It’s inspired by it (local learning, modulation, inhibitory control), not a 1:1 simulation. We keep only mechanisms that help learning & efficiency.

---

## Appendix A — Region API (reference impl)

> Place this as `src/python/region.py`. It depends on your existing `layer.py`, `neuron.py`, and `weight.py`.

```python
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Callable

from layer import Layer
from neuron import Neuron
from weight import Weight


class RegionBus:
    def __init__(self) -> None:
        self.inhibition_factor: float = 1.0
        self.modulation_factor: float = 1.0
        self.current_step: int = 0

    def decay(self) -> None:
        self.inhibition_factor = 1.0
        self.modulation_factor = 1.0
        self.current_step += 1


@dataclass
class InterLayerEdge:
    target: Neuron
    weight: Weight = field(default_factory=Weight)
    is_feedback: bool = False
    last_step: int = 0


@dataclass
class QueuedEvent:
    target: Neuron
    value: float


class Tract:
    """Bundle of inter-layer connections with a per-tick delivery queue."""
    def __init__(self, source: Layer, dest: Layer, region_bus: RegionBus, is_feedback: bool = False) -> None:
        self.source = source
        self.dest = dest
        self.region_bus = region_bus
        self.is_feedback = is_feedback
        self.edges: Dict[Neuron, List[InterLayerEdge]] = {}
        self.queue: List[QueuedEvent] = []
        self._hooked_sources: set[Neuron] = set()

    def wire_dense_random(self, probability: float) -> None:
        if probability <= 0.0:
            return
        from random import random
        for src in self.source.neurons:
            for dst in self.dest.neurons:
                if src is dst:
                    continue
                if random() >= probability:
                    continue
                edge = InterLayerEdge(target=dst, is_feedback=self.is_feedback)
                self.edges.setdefault(src, []).append(edge)
                if src not in self._hooked_sources:
                    src.register_fire_hook(self._make_source_hook(src))
                    self._hooked_sources.add(src)

    def _make_source_hook(self, src: Neuron) -> Callable[[float, Neuron], None]:
        def on_source_fire(input_value: float, source_neuron: Neuron) -> None:
            if source_neuron is not src:
                return
            edges = self.edges.get(src, [])
            for edge in edges:
                edge.weight.reinforce(
                    modulation_factor=self.region_bus.modulation_factor,
                    inhibition_factor=self.region_bus.inhibition_factor
                )
                fired = edge.weight.update_threshold(input_value)
                if fired:
                    self.queue.append(QueuedEvent(edge.target, input_value))
                    edge.last_step = self.region_bus.current_step
        return on_source_fire

    def flush(self) -> int:
        delivered = 0
        if not self.queue:
            return delivered
        pending, self.queue = self.queue, []
        for event in pending:
            event.target.on_input(event.value)
            delivered += 1
        return delivered

    def prune_edges(self, stale_window: int, min_strength: float) -> int:
        pruned = 0
        keep_map: Dict[Neuron, List[InterLayerEdge]] = {}
        for src, edges in self.edges.items():
            kept = []
            for edge in edges:
                is_stale = (self.region_bus.current_step - edge.last_step) > stale_window
                is_weak = edge.weight.strength_value < min_strength
                if is_stale and is_weak:
                    pruned += 1
                else:
                    kept.append(edge)
            if kept:
                keep_map[src] = kept
        self.edges = keep_map
        return pruned


class Region:
    """Layers + tracts with a stable two-phase tick."""
    def __init__(self, name: str) -> None:
        self.name = name
        self.layers: List[Layer] = []
        self.tracts: List[Tract] = []
        self.bus = RegionBus()
        self.input_ports: Dict[str, List[int]] = {}
        self.output_ports: Dict[str, List[int]] = {}

    def add_layer(self, excitatory_count: int, inhibitory_count: int, modulatory_count: int) -> int:
        layer = Layer(excitatory_count, inhibitory_count, modulatory_count)
        self.layers.append(layer)
        return len(self.layers) - 1

    def connect_layers(self, source_index: int, dest_index: int,
                       probability: float, feedback: bool = False) -> Tract:
        source = self.layers[source_index]
        dest = self.layers[dest_index]
        tract = Tract(source, dest, self.bus, is_feedback=feedback)
        tract.wire_dense_random(probability)
        self.tracts.append(tract)
        return tract

    def bind_input(self, port: str, layer_indices: List[int]) -> None:
        self.input_ports[port] = list(layer_indices)

    def bind_output(self, port: str, layer_indices: List[int]) -> None:
        self.output_ports[port] = list(layer_indices)

    def pulse_inhibition(self, factor: float) -> None:
        self.bus.inhibition_factor = factor

    def pulse_modulation(self, factor: float) -> None:
        self.bus.modulation_factor = factor

    def tick(self, port: str, value: float) -> Dict[str, float]:
        # Phase A
        for idx in self.input_ports.get(port, []):
            self.layers[idx].forward(value)
        # Phase B
        delivered = 0
        for tract in self.tracts:
            delivered += tract.flush()
        # Decay
        for layer in self.layers:
            layer.bus.decay()
        self.bus.decay()
        # Metrics
        total_slots = sum(len(n.slots) for layer in self.layers for n in layer.neurons)
        total_synapses = sum(len(n.outgoing) for layer in self.layers for n in layer.neurons)
        return {
            "delivered_events": float(delivered),
            "total_slots": float(total_slots),
            "total_synapses": float(total_synapses),
        }

    def prune(self, synapse_stale_window: int = 10_000, synapse_min_strength: float = 0.05,
              tract_stale_window: int = 10_000, tract_min_strength: float = 0.05) -> Dict[str, int]:
        pruned_syn = 0
        for layer in self.layers:
            for neuron in layer.neurons:
                before = len(neuron.outgoing)
                neuron.prune_synapses(self.bus.current_step, synapse_stale_window, synapse_min_strength)
                pruned_syn += before - len(neuron.outgoing)
        pruned_edges = sum(t.prune_edges(tract_stale_window, tract_min_strength) for t in self.tracts)
        return {"pruned_synapses": pruned_syn, "pruned_edges": pruned_edges}
```

> **Note:** this relies on two tiny additions already in `neuron.py`:
>
> 1. a list `self.fire_hooks` and
> 2. `register_fire_hook(hook)` method, and
> 3. calling those hooks at the end of `fire(...)`.
>    (Your current Python version already includes/accepts this.)

---

## Appendix B — Region demo

> Place this as `src/python/region_demo.py`.

```python
import random
from region import Region

def main():
    region = Region("vision")
    layer_in  = region.add_layer(40, 8, 4)
    layer_out = region.add_layer(30, 6, 3)

    region.bind_input("pixels", [layer_in])
    region.connect_layers(layer_in, layer_out, probability=0.10, feedback=False)
    region.connect_layers(layer_out, layer_in, probability=0.01, feedback=True)

    for step_index in range(2_000):
        value = random.random()
        metrics = region.tick("pixels", value)
        if (step_index + 1) % 200 == 0:
            print(f"[step {step_index+1}] delivered={metrics['delivered_events']:.0f} "
                  f"slots={metrics['total_slots']:.0f} syn={metrics['total_synapses']:.0f}")

    print("Pruning summary:", region.prune())

if __name__ == "__main__":
    main()
```

---

### That’s it

You now have the **reference Python flow**: slots → neurons → layers → regions with **tracts** and a **two‑phase tick**. From here we can add **growth triggers** (spawn a new layer when slot/synapse creation surges), richer logging (CSV/plots), and mirror the Region API in **Java/Mojo/C++**.

If you want, I can also add a “Quickstart diagram” (ASCII) or a small PNG to this doc.
