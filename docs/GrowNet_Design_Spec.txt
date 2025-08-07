# GrowNet - Theory of Change

## 1 · Scope & Naming

* **Project / model name** **GrowNet**
* **Design document title** **“GrowNet: Theory of Change”**
  (this file doubles as the authoritative spec)

---

## 2 · Architectural Overview

```
          +-------------------------  data stream  -------------------------+
          |                                                               |
          v                                                               |
   +----------------+       (fan‑out per input)        +----------------+  |
   |   Layer[N]     |  --x--> ExcitatoryNeuron*  -->   |  Layer[N+1]    |  |
   | (mixed types)  |        InhibitoryNeuron*         |  ...           |  |
   +----------------+        ModulatoryNeuron*         +----------------+  |
          ^                                                               |
          +---------------------  back‑prop‑free  ------------------------+
```

* **Neuron = container** of *independent threshold sub‑units* (“slots”, aka slots).
* **No global error signal**: learning is local, achieved via non‑linear reinforcement of slot weights.
* **Three neuron phenotypes** control network dynamics:

| Type                 | Default action on spike                                                               | Biological analogue            | Implementation hook                                                                             |
| -------------------- | ------------------------------------------------------------------------------------- | ------------------------------ | ----------------------------------------------------------------------------------------------- |
| **ExcitatoryNeuron** | Propagate spike to downstream connections (OR‑gate across its own slots).             | Pyramidal cells                | Already matches current behaviour.                                                              |
| **InhibitoryNeuron** | Multiply downstream slot‑strengths by γ < 1 for Δ T timesteps (“lateral inhibition”). | GABA interneurons              | `onSpike()` emits an **inhibition event** into a shared bus.                                    |
| **ModulatoryNeuron** | Adjust learning‑rate α of downstream weights (e.g., scale `stepVal`).                 | Dopaminergic / neuromodulators | Emits a **modulation event** into the bus: downstream weights read the factor when reinforcing. |

All three extend the common **Neuron** base and therefore share slot logic.

---

## 3 · Data Structures

### 3.1 `Weight`  (aka Compartment)

| Field                | Type              | Purpose                                                  |
| -------------------- | ----------------- | -------------------------------------------------------- |
| `strength`           | `float` (−1 … +1) | Synaptic efficacy; `reinforce()` clamps via smooth‑step. |
| `hitCount`           | `int`             | Saturation at 10 000 ⇒ weight freezes.                   |
| **Adaptive‑θ state** |                   | now lives **inside** `Weight`, per Sardi et al.          |
|   `theta`            | `float`           | Current threshold.                                       |
|   `emaRate`          | `float`           | Exponential avg of recent fires.                         |
|   `seenFirst`        | `bool`            | Whether T0 imprint executed.                             |

### 3.2 `Neuron` (base)

| Field          | Type                       | Purpose                                                              |
| -------------- | -------------------------- | -------------------------------------------------------------------- |
| `slots` | `Dict[int, Weight]`        | Key = `slotId` (rounded %‑delta or later, learned direction). |
| `downstream`   | `Dict[str, Weight]`        | Outgoing synapses; same object as in `slots`.                 |
| `typeTag`      | `enum {Excit, Inhib, Mod}` | Runtime behaviour switch.                                            |

### 3.3 `Inhibition / Modulation Bus`

A lightweight **event queue** per layer:

```python
class LateralBus:
    inhibitionLevel: float = 0.0    # decays each tick
    modulationFactor: float = 1.0   # resets to 1.0 each tick
```

* Every neuron reads `bus` before `reinforce()` to scale `stepVal` (modulation)
  and after spiking to apply `strength *= inhibitionLevel` (inhibition).

---

## 4 · Algorithms

### 4.1 Local Learning (per slot)

```python
def reinforce(weight: Weight):
    # apply neuromodulation
    effectiveStep = weight.stepVal * bus.modulationFactor
    # strengthen
    if weight.hitCount < HIT_SAT:
        weight.strength = smoothClamp(weight.strength + effectiveStep, -1, 1)
        weight.hitCount += 1
```

### 4.2 Adaptive Threshold (T0 + T2 Hybrid)

Exactly the code we already have, but **inside Weight**:

```python
if not weight.seenFirst:
    weight.theta = abs(inputVal) * (1 + EPS)
    weight.seenFirst = True

fired = weight.strength > weight.theta

weight.emaRate = (1 - BETA) * weight.emaRate + BETA * fired
weight.theta  += ETA * (weight.emaRate - R_STAR)
```

### 4.3 Neuron Spike Handling

```python
def onInput(neuron, x):
    for weight in neuron.slotsFor(x):
        weight.reinforce()
        if weight.strength > weight.theta:
            neuron.fire(x)
            break    # OR‑gate: first slot wins

def fire(neuron, x):
    if neuron.typeTag == EXCIT:
        propagateDownstream(neuron, x)
    elif neuron.typeTag == INHIB:
        bus.inhibitionLevel = gamma   # e.g., 0.7
    elif neuron.typeTag == MOD:
        bus.modulationFactor = kappa  # e.g., 1.5
```

---

## 5 · File / Module Layout

```
src/
├─ python/
│   ├─ math_utils.py             # smoothClamp, roundTwo
│   ├─ weight.py                 # Weight class
│   ├─ neuron_base.py            # common Neuron logic
│   ├─ neuron_exc.py             # ExcitatoryNeuron
│   ├─ neuron_inh.py             # InhibitoryNeuron
│   ├─ neuron_mod.py             # ModulatoryNeuron
│   ├─ layer.py                  # maintains LateralBus
│   └─ train_*                   # experiment runners
├─ mojo/                         # mirror same split, later GPU kernels
└─ docs/
    └─ GrowNet_Theory_of_Change.md
```

---

## 6 · Open Questions / To‑Do

| Topic                                                                                       | Decision needed by                    |
| ------------------------------------------------------------------------------------------- | ------------------------------------- |
| Exact **γ (inhibition decay)** and **κ (modulation scale)** values                          | after first ablation                  |
| Wiring pattern: random ratio (e.g., 80 % excit, 15 % inhib, 5 % mod) vs. learned assignment | before Tier‑2 continual‑learning test |
| Event‑bus time constant (how many timesteps inhibition lasts)                               | during profiling phase                |

---

## 7 · Implementation Roadmap (updated)

| Milestone                                                         | Owner     | Target date     |
| ----------------------------------------------------------------- | --------- | --------------- |
| **M1**: Slot‑level θ refactor (Python + Mojo) ✔                   | assistant | today           |
| **M2**: Add three neuron subclasses (Python first)                | assistant | +1 day          |
| **M3**: Run E‑00 multi‑type config (Excit‑only first, then mixed) | you       | +2 days         |
| **M4**: Implement Inhibitory + Modulatory behaviour on the bus    | assistant | +3 days         |
| **M5**: Growth‑trigger τ tuning                                   | both      | next sprint     |
| **M6**: Mojo GPU kernel for `reinforceCompartment`                | assistant | after profiling |

---

### Next Immediate Action

I will:

1. Push **M1 commit** (slot‑level thresholds, updated doc header).
2. Generate stub Python classes for `ExcitatoryNeuron`, `InhibitoryNeuron`, `ModulatoryNeuron` that inherit all logic from `NeuronBase` and override `fire()`.

You will:

* Pull the commit, run the default **Excitatory‑only** experiment, and confirm baseline behaviour is unchanged.

As soon as that’s green we wire in inhibition & modulation dynamics.

Sound good?
