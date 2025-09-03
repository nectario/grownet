Below is a complete, reorganized **`docs/FAQ.md`** you can drop into your repo. It keeps all the substance from your current draft, but groups related ideas, adds crisp “quick answers,” and highlights the **delta‑based slot choice** and **two‑phase tick** model up front. (Source: reorganized from your latest FAQ draft.) 

------

# GrowNet – Frequently Asked Questions (FAQ)

*A practical, plain‑language guide to what GrowNet is, how it works, and how to use it.*

> **One‑sentence version:**
>  **GrowNet** is an **AI research** project exploring lightweight, neurally inspired learning where simple neurons keep small **memory slots** and learn **locally** on each event—no global backprop—so the system can adapt quickly, stay interpretable, and **grow** over time.

------

## Table of Contents

**Quick answers**

1. [What is a tick?](https://chatgpt.com/g/g-p-68921663c4f881918135999b40a61416-grownet/c/68a3703b-d498-832a-8eba-9167923770cd#what-is-a-tick)
2. [How do ticks work (two‑phase model)?](https://chatgpt.com/g/g-p-68921663c4f881918135999b40a61416-grownet/c/68a3703b-d498-832a-8eba-9167923770cd#how-do-ticks-work-two-phase-model)
3. [What is a port? Why “ports‑as‑edges”?](https://chatgpt.com/g/g-p-68921663c4f881918135999b40a61416-grownet/c/68a3703b-d498-832a-8eba-9167923770cd#what-is-a-port-why-ports-as-edges)
4. [How does GrowNet count “delivered events”?](https://chatgpt.com/g/g-p-68921663c4f881918135999b40a61416-grownet/c/68a3703b-d498-832a-8eba-9167923770cd#how-does-grownet-count-delivered-events)

**Core concepts**

5. [What are “slots”? (delta‑based slot choice)](https://chatgpt.com/g/g-p-68921663c4f881918135999b40a61416-grownet/c/68a3703b-d498-832a-8eba-9167923770cd#what-are-slots-delta-based-slot-choice)
6. [What are **frozen slots** and why use them?](https://chatgpt.com/g/g-p-68921663c4f881918135999b40a61416-grownet/c/68a3703b-d498-832a-8eba-9167923770cd#what-are-frozen-slots-and-why-use-them)
7. [What is **Temporal Focus**?](https://chatgpt.com/g/g-p-68921663c4f881918135999b40a61416-grownet/c/68a3703b-d498-832a-8eba-9167923770cd#what-is-temporal-focus)
8. [What is **Spatial Focus**?](https://chatgpt.com/g/g-p-68921663c4f881918135999b40a61416-grownet/c/68a3703b-d498-832a-8eba-9167923770cd#what-is-spatial-focus)
9. [How do **2D bins** work?](https://chatgpt.com/g/g-p-68921663c4f881918135999b40a61416-grownet/c/68a3703b-d498-832a-8eba-9167923770cd#how-do-2d-bins-work)
10. [What does `connect_layers_windowed(...)` do, and what does it return?](https://chatgpt.com/g/g-p-68921663c4f881918135999b40a61416-grownet/c/68a3703b-d498-832a-8eba-9167923770cd#what-does-connect_layers_windowed-do-and-what-does-it-return)

**Learning signals & buses**

11. [What are buses? How does a modulatory neuron affect many neurons at once?](https://chatgpt.com/g/g-p-68921663c4f881918135999b40a61416-grownet/c/68a3703b-d498-832a-8eba-9167923770cd#what-are-buses-how-does-a-modulatory-neuron-affect-many-neurons-at-once)
12. [Can buses simulate dopamine‑like signals?](https://chatgpt.com/g/g-p-68921663c4f881918135999b40a61416-grownet/c/68a3703b-d498-832a-8eba-9167923770cd#can-buses-simulate-dopamine-like-signals)

**Using GrowNet**

13. [How do I enable spatial slotting in practice?](https://chatgpt.com/g/g-p-68921663c4f881918135999b40a61416-grownet/c/68a3703b-d498-832a-8eba-9167923770cd#how-do-i-enable-spatial-slotting-in-practice)
14. [How do I freeze/unfreeze a slot?](https://chatgpt.com/g/g-p-68921663c4f881918135999b40a61416-grownet/c/68a3703b-d498-832a-8eba-9167923770cd#how-do-i-freezeunfreeze-a-slot)
15. [What metrics can I inspect per tick?](https://chatgpt.com/g/g-p-68921663c4f881918135999b40a61416-grownet/c/68a3703b-d498-832a-8eba-9167923770cd#what-metrics-can-i-inspect-per-tick)
16. [Why no pooling layers?](https://chatgpt.com/g/g-p-68921663c4f881918135999b40a61416-grownet/c/68a3703b-d498-832a-8eba-9167923770cd#why-no-pooling-layers)

**Parity, troubleshooting, demos**

17. [Language parity notes (Python, C++, Java, Mojo)](https://chatgpt.com/g/g-p-68921663c4f881918135999b40a61416-grownet/c/68a3703b-d498-832a-8eba-9167923770cd#language-parity-notes-python-c-java-mojo)
18. [Troubleshooting: common C++ build errors/warnings](https://chatgpt.com/g/g-p-68921663c4f881918135999b40a61416-grownet/c/68a3703b-d498-832a-8eba-9167923770cd#troubleshooting-common-c-build-errorswarnings)
19. [Demos & tests: how do I run them quickly?](https://chatgpt.com/g/g-p-68921663c4f881918135999b40a61416-grownet/c/68a3703b-d498-832a-8eba-9167923770cd#demos--tests-how-do-i-run-them-quickly)

**Reference**

20. [Parameter cheat‑sheet for slotting](https://chatgpt.com/g/g-p-68921663c4f881918135999b40a61416-grownet/c/68a3703b-d498-832a-8eba-9167923770cd#parameter-cheat-sheet-for-slotting)

------

## Quick answers

### What is a tick?

A **tick** is one discrete update step. You drive exactly **one bound input edge** for a named port—either a scalar (`tick(port, value)`) or a 2D frame (`tick_2d(port, frame)`)—let activity propagate through wiring, then run post‑tick housekeeping (bus decays/resets, metrics). Think: **drive → propagate → wrap‑up**. 

### How do ticks work (two‑phase model)?

**Phase‑A (Drive & Propagate)**: the bound edge receives the input once; neurons pick/update slots and may **fire**; spikes fan out through synapses/tracts.
 **Phase‑B (Post‑actions / `end_tick`)**: each layer decays **inhibition** (multiplicative), resets **modulation** to 1.0, runs housekeeping; region tallies metrics (optionally spatial metrics for 2D). The split keeps behavior predictable. 

### What is a port? Why “ports‑as‑edges”?

A **port** is a named input binding: `port → InputEdge` (scalar) or `port → InputLayer2D` (image). Each tick **drives the bound edge once**; all downstream activity is due to wiring. This keeps input semantics and metrics clear. 

### How does GrowNet count “delivered events”?

**One tick = one delivered event** to the bound input edge. Fan‑out doesn’t increase the count. (Some legacy compatibility toggles exist; default is one per tick.) 

------

## Core concepts

### What are “slots”? (delta‑based slot choice)

A **slot** is a tiny, per‑neuron memory cell that specializes to a **range of change** in its input. On each event the neuron:

1. chooses a **baseline** $B$ (the **anchor**),
2. computes a **percent delta** $\Delta\% = 100 \cdot \frac{|x - B|}{\max(|B|,\varepsilon)}$,
3. maps that delta into a **bin**: $\text{slotId}=\big\lfloor \Delta\% / \text{bin\_width\_\%} \big\rfloor$,
4. **selects/creates** the slot (respecting `slot_limit`) and **reinforces** it (scaled by the layer’s modulation bus). If the slot crosses threshold, the neuron **fires**.

> **Why deltas?** They’re **scale‑invariant** and easy to interpret (“~20–30% jump” vs. a raw value). In spatial mode the same idea applies per axis (row/col). 

> **Previous‑step baseline?** The default is **anchor‑based** (stable reference like FIRST/ORIGIN). You can add a “compare‑to‑previous” mode later; it uses the same formula but sets $B$ to the **last input** (handy for motion/speed), typically with a small minimum‑step or smoothing. 

### What are **frozen slots** and why use them?

A **frozen slot** still matches and can fire, but **ignores** reinforcement (and any modulation scaling). Use them to lock in “reference patterns,” protect safety anchors, or stage a curriculum (learn → freeze → learn the next thing). 

### What is **Temporal Focus**?

GrowNet’s scalar slotting: compare each input to a scalar **anchor** (default **FIRST**), compute the **percent delta**, then pick the bin by width (e.g., 10%/bin). Slots become detectors for **ranges of change** (“small,” “medium,” “large”), not absolute values. 

### What is **Spatial Focus**?

The same discipline extended to **2D**. Each neuron anchors at a reference **(row, col)**—**FIRST** (default) or **ORIGIN**—then incoming events choose a **(rowBin, colBin)** by **per‑axis percent deltas**. Often combined with **`connect_layers_windowed`** for deterministic 2D wiring. Spatial focus is **opt‑in** per receiving layer. 

### How do **2D bins** work?

With anchor $(a_r,a_c)$ and pixel $(r,c)$:

- $\Delta\%_r = 100 \cdot \frac{|r-a_r|}{\max(|a_r|,\varepsilon)}$,
- $\Delta\%_c = 100 \cdot \frac{|c-a_c|}{\max(|a_c|,\varepsilon)}$,

then

- $\text{rowBin}=\big\lfloor \Delta\%_r / \text{row\_bin\_width\_\%} \big\rfloor$,
- $\text{colBin}=\big\lfloor \Delta\%_c / \text{col\_bin\_width\_\%} \big\rfloor$.

Use $\varepsilon \approx 1.0$ spatially so bins don’t explode at the origin. The resulting $(\text{rowBin},\text{colBin})$ keys the slot (respect `slot_limit`). 

### What does `connect_layers_windowed(...)` do, and what does it return?

It wires an `InputLayer2D` to a destination using sliding windows:

- **If dest is `OutputLayer2D`**: each window forwards to its **center** output neuron (center = floor(midpoint; clamped to bounds; same rule for even kernels).
- **If dest is a generic layer**: every pixel that participates in any window connects to the destination (deterministic fan‑out for now).

**Return value:** number of **unique source subscriptions** (distinct source pixels that appear in at least one window)—**not** the raw (src,dst) edge count. 

------

## Learning signals & buses

### What are buses? How does a modulatory neuron affect many neurons at once?

Each **layer** has a **bus** with short‑lived factors:

- **Inhibition** (decays multiplicatively each tick),
- **Modulation** (resets to 1.0 each tick).

A modulatory neuron (or controller) nudges the bus once; **all neurons** in that layer read the same modulation factor when reinforcing slots. That’s how a single source can shape **many** targets in one tick. 

### Can buses simulate dopamine‑like signals?

Yes. Treat dopamine bursts as **transient modulation** (>1 for boosts, <1 for dips). It’s **phasic**—resets each tick—so it aligns well with reward pulses. **Frozen slots** ignore these pulses by design, which is useful for stabilizing anchors. (You can add tonic components or eligibility traces later if needed.) 

------

## Using GrowNet

### How do I enable spatial slotting in practice?

**Python**

```python
region = Region("spatial")
l_in  = region.add_input_layer_2d(8, 8, gain=1.0, epsilon_fire=0.01)
l_hid = region.add_layer(excitatory_count=12, inhibitory_count=0, modulatory_count=0)

# Enable spatial focus in the receiving layer
for n in region.get_layers()[l_hid].get_neurons():
    n.slot_cfg.spatial_enabled   = True
    n.slot_cfg.row_bin_width_pct = 50.0
    n.slot_cfg.col_bin_width_pct = 50.0

# Deterministic 2D wiring
region.connect_layers_windowed(l_in, l_hid, kernel_h=3, kernel_w=3, stride_h=2, stride_w=2, padding="valid")

region.bind_input("pixels", [l_in])
m = region.tick_2d("pixels", frame)  # frame = list of rows
```

**C++ parity**: use `Region::connectLayersWindowed(...)` similarly; return is **unique sources**. 

### How do I freeze/unfreeze a slot?

**Python**

```python
n.freeze_slot(slot_id)
# ... later ...
n.unfreeze_slot(slot_id)
```

**Java / C++ / Mojo** expose equivalent `freezeSlot(int)` / `unfreezeSlot(int)` helpers per neuron. A frozen slot **still matches/fires** but **doesn’t adapt** and **ignores** modulation when reinforcing. 

### What metrics can I inspect per tick?

**Core** (always on): `delivered_events`, `total_slots`, `total_synapses`.
 **Spatial** (flag or `GROWNET_ENABLE_SPATIAL_METRICS=1`): `active_pixels`, `centroid_row/col`, `bbox`. Spatial metrics prefer the **furthest downstream `OutputLayer2D`** frame; if that’s all zeros, they fall back to the **input frame**. 

### Why no pooling layers?

GrowNet isn’t a deep CNN; we avoid hard‑coded pooling to keep the model close to **event‑driven local learning**. Spatial Focus + windowed wiring already provide **coarse place coding** and aggregation without fixed pooling stages. 

------

## Language parity notes (Python, C++, Java, Mojo)

- **Python**: reference path with Spatial Focus, windowed wiring, demos, tests.
- **C++**: mirrors core features, deterministic windowed wiring, optional spatial metrics; designed for speed.
- **Java**: production‑friendly; uses the slot engine and unified bus decay.
- **Mojo**: parity stubs with growing coverage.

Minor behavioral differences may exist (e.g., stricter per‑edge gating in some Java paths vs. immediate fan‑out elsewhere). The code and docs aim to keep behavior **convergent** across languages. 

------

## Troubleshooting: common C++ build errors/warnings

**“invalid use of incomplete type ‘class Neuron’” from `SlotEngine.h`**
 Inline methods in `SlotEngine.h` touch `Neuron` while only a forward declaration is visible. Fix either by **including `Neuron.h`** at the top (watch for cycles) or by **moving** those method bodies into `SlotEngine.cpp` (then include `Neuron.h` there). 

**Misleading indentation (`if`/`for` one‑liners) in `Region.cpp`**
 Expand to blocks:

```cpp
if (r < rmin) { rmin = r; }
if (r > rmax) { rmax = r; }
```

**Demos referencing `Region::prune`**
 If you’re not using pruning yet, add a **no‑op stub** returning an empty `PruneSummary` so demos compile and run unchanged. 

------

## Demos & tests: how do I run them quickly?

**Python demo (moving dot / spatial)**

```bash
PYTHONPATH=src/python python src/python/demos/spatial_focus_demo.py
```

**Python tests**

```bash
pytest -q
# Optional spatial metrics:
GROWNET_ENABLE_SPATIAL_METRICS=1 pytest -q
```

**C++ windowed‑wiring smoke (guarded)**

```bash
g++ -std=c++17 -DGROWNET_WINDOWED_WIRING_SMOKE -Isrc/cpp \
    src/cpp/*.cpp src/cpp/tests/WindowedWiringSmoke.cpp -o win_smoke
./win_smoke
```



------

## Parameter cheat‑sheet for slotting

- **`bin_width_pct`** (scalar), **`row_bin_width_pct` / `col_bin_width_pct`** (2D): width of each delta bin, in percent.
- **`slot_limit`**: max number of slots per neuron; beyond this, a **fallback bin** is reused to cap growth.
- **`epsilon_scale`**: lower bound in the denominator to avoid division by zero (use **1.0** for spatial to prevent huge bins at the origin).
- **Anchors**: scalar uses **FIRST** by default; spatial supports **FIRST** and **ORIGIN** (and could add a **PREVIOUS** baseline mode later). 

------

### Still have questions?

If something feels unclear—or you want tiny examples (dopamine‑like reward loop, frozen‑slot curriculum, custom 2D binning)—add a note. GrowNet aims to stay **simple, inspectable, and hackable**. 

------