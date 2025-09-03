Here’s a ready‑to‑drop **`docs/FAQ.md`** for GrowNet.

------

# GrowNet – Frequently Asked Questions (FAQ)

*A practical, plain‑language guide to how GrowNet works, why it’s different, and how to use key features.*

> **What is GrowNet, in one sentence?**
>  **GrowNet** is an **AI research** project exploring lightweight, neurally‑inspired learning where simple neurons keep small **memory slots** and learn **locally** on each event, rather than using heavy backpropagation across the whole network.

------

## Table of contents

1. [What is GrowNet? What problem does it try to solve?](https://chatgpt.com/g/g-p-68921663c4f881918135999b40a61416-grownet/c/68a3703b-d498-832a-8eba-9167923770cd#what-is-grownet-what-problem-does-it-try-to-solve)
2. [How is GrowNet different from deep learning?](https://chatgpt.com/g/g-p-68921663c4f881918135999b40a61416-grownet/c/68a3703b-d498-832a-8eba-9167923770cd#how-is-grownet-different-from-deep-learning)
3. [What are “slots”?](https://chatgpt.com/g/g-p-68921663c4f881918135999b40a61416-grownet/c/68a3703b-d498-832a-8eba-9167923770cd#what-are-slots)
4. [What are **frozen slots** and why would I use them?](https://chatgpt.com/g/g-p-68921663c4f881918135999b40a61416-grownet/c/68a3703b-d498-832a-8eba-9167923770cd#what-are-frozen-slots-and-why-would-i-use-them)
5. [What is **Temporal Focus**?](https://chatgpt.com/g/g-p-68921663c4f881918135999b40a61416-grownet/c/68a3703b-d498-832a-8eba-9167923770cd#what-is-temporal-focus)
6. [What is **Spatial Focus**?](https://chatgpt.com/g/g-p-68921663c4f881918135999b40a61416-grownet/c/68a3703b-d498-832a-8eba-9167923770cd#what-is-spatial-focus)
7. [How do 2D bins work?](https://chatgpt.com/g/g-p-68921663c4f881918135999b40a61416-grownet/c/68a3703b-d498-832a-8eba-9167923770cd#how-do-2d-bins-work)
8. [What does `connect_layers_windowed(...)` do and what does it return?](https://chatgpt.com/g/g-p-68921663c4f881918135999b40a61416-grownet/c/68a3703b-d498-832a-8eba-9167923770cd#what-does-connect_layers_windowed-do-and-what-does-it-return)
9. [How do ticks work? (two‑phase tick model)](https://chatgpt.com/g/g-p-68921663c4f881918135999b40a61416-grownet/c/68a3703b-d498-832a-8eba-9167923770cd#how-do-ticks-work-two-phase-tick-model)
10. [What are buses? How does a modulatory neuron affect many neurons at once?](https://chatgpt.com/g/g-p-68921663c4f881918135999b40a61416-grownet/c/68a3703b-d498-832a-8eba-9167923770cd#what-are-buses-how-does-a-modulatory-neuron-affect-many-neurons-at-once)
11. [Can buses simulate dopamine‑like signals?](https://chatgpt.com/g/g-p-68921663c4f881918135999b40a61416-grownet/c/68a3703b-d498-832a-8eba-9167923770cd#can-buses-simulate-dopamine-like-signals)
12. [How do I enable spatial slotting in practice?](https://chatgpt.com/g/g-p-68921663c4f881918135999b40a61416-grownet/c/68a3703b-d498-832a-8eba-9167923770cd#how-do-i-enable-spatial-slotting-in-practice)
13. [How do I freeze/unfreeze a slot?](https://chatgpt.com/g/g-p-68921663c4f881918135999b40a61416-grownet/c/68a3703b-d498-832a-8eba-9167923770cd#how-do-i-freezeunfreeze-a-slot)
14. [What metrics can I inspect per tick?](https://chatgpt.com/g/g-p-68921663c4f881918135999b40a61416-grownet/c/68a3703b-d498-832a-8eba-9167923770cd#what-metrics-can-i-inspect-per-tick)
15. [Why no pooling layers?](https://chatgpt.com/g/g-p-68921663c4f881918135999b40a61416-grownet/c/68a3703b-d498-832a-8eba-9167923770cd#why-no-pooling-layers)
16. [Does GrowNet support multiple languages? Any parity notes?](https://chatgpt.com/g/g-p-68921663c4f881918135999b40a61416-grownet/c/68a3703b-d498-832a-8eba-9167923770cd#does-grownet-support-multiple-languages-any-parity-notes)
17. [Troubleshooting: common C++ build errors/warnings](https://chatgpt.com/g/g-p-68921663c4f881918135999b40a61416-grownet/c/68a3703b-d498-832a-8eba-9167923770cd#troubleshooting-common-c-build-errorswarnings)
18. [Demos & tests: how do I run them quickly?](https://chatgpt.com/g/g-p-68921663c4f881918135999b40a61416-grownet/c/68a3703b-d498-832a-8eba-9167923770cd#demos--tests-how-do-i-run-them-quickly)

------

## What is GrowNet? What problem does it try to solve?

GrowNet explores **local, incremental learning** inspired by simple biological circuits. Each neuron maintains a handful of **slots** (think “labeled drawers”). When inputs arrive, the neuron picks a slot (or creates one), updates it, and decides whether to **fire**. This aims to be **data‑efficient**, **fast to adapt**, and easier to reason about than large, opaque models.

------

## How is GrowNet different from deep learning?

- **No backpropagation** across deep stacks. Learning is **local** (per neuron/slot) and **event‑by‑event**.
- **Growth** happens by adding slots (and later, neurons/layers), not by nudging millions of weights.
- **Interpretability**: slots are small, explicit memories you can inspect or **freeze**.
- **Multi‑language** reference implementations (Python, C++, Mojo, Java) designed to be clear and comparable.

------

## What are “slots”?

A **slot** is a tiny, per‑neuron memory cell that specializes to a **range of change** in its input. Each neuron keeps a small map of slots (bins). On every event:

1. The neuron picks a **baseline** $B$ to compare the current input $x$ against.

   - **Scalar (Temporal Focus):** by default **FIRST‑anchor** — the first meaningful value the neuron saw for this context.
   - **2D (Spatial Focus):** baseline is an anchor **(row, col)**; by default **FIRST**, or **ORIGIN (0,0)** if configured.

2. It computes a **percent delta** from the baseline (scale‑free):

   Δ%=100×∣x−B∣max⁡(∣B∣,ε)\Delta\% = 100 \times \frac{|x - B|}{\max(|B|, \varepsilon)}

   The small $\varepsilon$ avoids division by zero (for spatial, a sensible epsilon like **1.0** is used to prevent exploding bins at the origin).

3. It maps that delta into a **bin** using a width parameter (e.g., 10% per bin):

   slotId=⌊Δ%bin_width_%⌋\text{slotId} = \left\lfloor \frac{\Delta\%}{\text{bin\_width\_\%}} \right\rfloor

   For **2D**, this happens **per axis** (row and column), yielding a tuple $(\text{rowBin}, \text{colBin})$.

4. It **selects or creates** that slot (respecting `slot_limit`) and **reinforces** it (scaled by the layer’s modulation bus). If the slot’s strength crosses a threshold, the neuron **fires**.

This **delta‑based choice** is the important part: slots don’t memorize raw values; they specialize to **how much** and **where** things change relative to an anchor. That makes slotting robust to scale and more interpretable: “this slot fires for ~20–30% jumps” (or “offsets ~1–2 row‑bins to the right”), instead of “this slot fires at absolute value 0.37”.

Frozen slots fit neatly into this picture: a **frozen** slot still matches and can fire, but **ignores** reinforcement and modulation, keeping its learned boundary stable.

------

## What are **frozen slots** and why would I use them?

A **frozen slot** is a slot that stops adapting. It still participates in matching/firing, but:

- **Ignores** modulatory gain (e.g., dopamine‑like pulses).
- **Ignores** inhibition‑driven adjustments.
- Keeps its state stable—useful for **reference patterns**, safety anchors, or curriculum steps.

Typical uses:

- Lock in a template once it proves reliable.
- Protect “landmarks” while the rest of the network continues to adapt.

------

## What is **Temporal Focus**?

Temporal Focus is the **scalar slotting strategy**. It picks a **bin of change** for each input based on **percent delta** from an **anchor**:

- **Baseline (default):** **FIRST‑anchor** — the neuron records the first meaningful input as its reference $B$.
- **Delta:** $\Delta\% = 100 \times \frac{|x - B|}{\max(|B|,\varepsilon)}$ (scale‑free).
- **Bin:** $\text{slotId} = \left\lfloor \frac{\Delta\%}{\text{bin\_width\_\%}} \right\rfloor$.

This gives you interpretable, range‑like detectors (“small change”, “medium jump”, “big jump”) without global training. The same discipline underlies spatial slotting; there, you compute per‑axis deltas against a 2D anchor.

> **Why percent deltas?**
>  They’re **scale‑invariant** and easy to reason about (“~10% change”). If the input scale drifts, your slot boundaries still mean the same thing.What is **Spatial Focus**?

Spatial Focus extends slotting to **2D**:

- Each neuron anchors to a reference **(row, col)** (FIRST or ORIGIN).
- Incoming events use **per‑axis percent deltas** to choose a **(rowBin, colBin)** slot.
- Works well with **InputLayer2D** and the **windowed wiring** helper.

Spatial Focus is **opt‑in** (off by default). Enable it per receiving neuron/layer.



## **Can I choose deltas vs. previous value instead of an anchor?**

Conceptually, yes; there are two common baselines:

- **Anchor‑based (current default):** compare to a **fixed anchor** like FIRST, giving stable, interpretable bands (“~20–30% from my original reference”).
- **Previous‑step delta (optional design):** compare to the **last input**, emphasizing *moment‑to‑moment* change (“speed of change”).

GrowNet’s **default** is anchor‑based (FIRST for scalar; FIRST/ORIGIN for spatial). If you later want a **previous‑step** mode, it’s straightforward to add as a toggle (e.g., a `baseline_mode="PREVIOUS"` knob in the slot config) and would use the same delta → bin formula, just with $B$ set to the **prior input** instead of the anchor. In practice, previous‑step deltas often benefit from a small **low‑pass** or **minimum step** to reduce noise.

------

## How do 2D bins work?

Given an anchor $(a_r, a_c)$ and a pixel location $(r, c)$:

1. Compute per‑axis **percent deltas** (with a safe epsilon, typically **1.0**):

   Δ%r=100×∣r−ar∣max⁡(∣ar∣,ε),Δ%c=100×∣c−ac∣max⁡(∣ac∣,ε)\Delta\%_r = 100 \times \frac{|r - a_r|}{\max(|a_r|,\varepsilon)}, \quad \Delta\%_c = 100 \times \frac{|c - a_c|}{\max(|a_c|,\varepsilon)}

2. Map each delta to a bin:

   rowBin=⌊Δ%rrow_bin_width_%⌋,colBin=⌊Δ%ccol_bin_width_%⌋\text{rowBin} = \left\lfloor \frac{\Delta\%_r}{\text{row\_bin\_width\_\%}} \right\rfloor,\quad \text{colBin} = \left\lfloor \frac{\Delta\%_c}{\text{col\_bin\_width\_\%}} \right\rfloor

3. Use the tuple $(\text{rowBin}, \text{colBin})$ to **select/create** the slot (subject to `slot_limit`).

Anchoring options:

- **FIRST (default):** lock onto the first salient $(r,c)$ the neuron sees.
- **ORIGIN:** treat $(0,0)$ as the anchor (handy for certain coordinate frames).

Just like in the scalar case, this is a **delta choice** policy: spatial slots detect *how far* and *in which directions* activity is from the reference, not absolute coordinates.

------

## What does `connect_layers_windowed(...)` do and what does it return?

It wires an `InputLayer2D` to a destination deterministically using sliding **windows**:

- **If dest is `OutputLayer2D`**: each window forwards to the **center** output neuron
   (center = floor(midpoint; clamped to image bounds; same rule for even kernels).
- **If dest is a generic layer**: every pixel that participates in any window is connected to the destination (deterministic fan‑out today).

**Return value:** the number of **unique source subscriptions** (i.e., distinct source pixels that appear in at least one window).
 It is **not** the raw count of (src, dst) edges.

------

## What are buses? How does a modulatory neuron affect many neurons at once?

Each **layer** has a **bus** carrying two short‑lived factors:

- **Inhibition** (decays multiplicatively each tick).
- **Modulation** (resets to `1.0` each tick).

A **modulatory neuron** (or external controller) writes **once** to the bus on a tick; **every neuron in the layer** reads it when reinforcing slots. That’s how one signal can shape learning **broadcast‑style**.



---

## What is a “tick”?

A **tick** is one discrete update step. You call `tick(port, value)` for scalar input or `tick_2d(port, frame)` for images. A tick:

* drives **exactly one bound input edge** for the named port,
* lets activity propagate through wired layers,
* then performs post‑tick housekeeping (decays, resets, metrics).

Think of it as: **drive → propagate → wrap up**.



## How do ticks work? (two‑phase tick model)

Every tick is split into:

1. **Phase‑1: Drive/propagate**
   - You drive a **port** (an “edge layer”) once (e.g., `tick(...)` or `tick_2d(...)`).
   - Activity flows forward via wiring; neurons **reinforce** selected slots and may **fire**.
2. **Phase‑2: Post‑actions (end‑of‑tick)**
   - **Housekeeping**: buses decay, modulation resets, neurons do any per‑tick cleanup.
   - **Metrics**: the system tallies delivered events, slots, synapses, optional spatial metrics.

This simple split mirrors “process the moment” → “settle/reset,” and makes behavior predictable.



---

## What exactly happens during a tick?

**Phase A — Drive & propagate (immediate effect)**

1. The **port’s bound input edge** receives the value/frame once.
2. Source neurons update their **slots** and may **fire**.
3. Spikes fan out over existing **synapses/tracts** to downstream neurons, which in turn run their own input logic and may fire.

**Phase B — Post actions (end‑of‑tick)**
4\) Each layer runs `end_tick` housekeeping:

* **Inhibition** on the lateral bus **decays multiplicatively** (e.g., ×0.90).
* **Modulation** on the bus **resets** to 1.0 (baseline).
* Any per‑neuron post‑tick maintenance happens here.

5. The region aggregates/update **metrics** (e.g., counts, optional spatial stats if enabled).

This two‑phase structure keeps behavior predictable: all causality for a tick is resolved **before** decays/resets.

---

## What’s the difference between `tick(...)` and `tick_2d(...)`?

* `tick(port, value)` drives a **scalar** into the bound **InputEdge** (temporal focus).
* `tick_2d(port, frame)` drives a **2D frame** into an **InputLayer2D** edge (spatial focus).

  * If you used **windowed wiring**, the source pixels are mapped deterministically to destinations (e.g., to the center output neuron per window).
  * Downstream layers can use **spatial slotting** (`on_input_2d`) so slots specialize to **2D deltas** (row/col bins).

Both share the same two‑phase tick lifecycle.

---

## How does GrowNet count “delivered events” per tick?

**One tick = one delivered event** to the bound input edge. Even if fan‑out yields many downstream spikes, the region’s `delivered_events` counter reflects **the one edge drive** that started this tick. (There’s a legacy compatibility mode in some setups, but the default behavior is “one per tick.”)

---

## What is a “port”? Why “ports‑as‑edges”?

Ports are **named input bindings**. You bind `port → InputEdge` (scalar) or `port → InputLayer2D` (image). On each tick the region **drives that edge once**, and all downstream activity is due to wiring. This keeps input semantics clear and metrics interpretable.

---

## What happens inside a neuron during Phase A?

On `on_input(...)` (scalar) or `on_input_2d(...)` (2D), the neuron:

1. Chooses a **baseline** (anchor) and computes a **percent delta** from it.
2. Maps that delta to a **slot/bin** (scalar: one id; 2D: row/col tuple).
3. **Selects/creates** the slot (respecting `slot_limit`).
4. **Reinforces** it, scaled by the layer’s **modulation** bus.
5. If the slot’s strength **crosses threshold**, the neuron **fires** and fans out to its targets.

> See the “delta‑based slot choice” question earlier in the FAQ for details and formulas.

---

## What is `end_tick` (post‑tick) and why is it separate?

`end_tick` runs **after** all propagation for the current tick finishes. It:

* **decays inhibition** (e.g., ×0.90),
* **resets modulation** to 1.0,
* performs light per‑neuron housekeeping.

Separating this phase guarantees that **all neurons see the same bus state during Phase A**, then the system **relaxes** at the tick boundary.

---

## How do inhibition and modulation combine within a tick?

They live on a **per‑layer lateral bus**:

* **Inhibition** is a **multiplier toward 0** that **persists** across ticks but **decays** each `end_tick`. It can make neurons less likely to fire **this tick and the next few**, depending on decay.
* **Modulation** is a **gain** for learning/reinforcement within the tick and then **resets** to baseline at `end_tick`. Think “temporary teaching signal.”

Multiple sources (e.g., modulatory neurons) can **add pulses** to the same bus; the actual update rule blends them (e.g., sum/clamp for modulation, accumulate then decay for inhibition).

---

## How can a single modulatory neuron affect many targets?

Two ways:

1. **Fan‑out synapses:** one spike fans to many destinations that **read** the current bus state when they process input.
2. **Bus update:** that neuron (or its layer) **nudges the layer’s bus** (e.g., `modulation += k` or `inhibition += k`) before others process input in Phase A. Because the bus is **shared**, that update influences **all** neurons in the layer for the current tick.

---

## What are “spatial metrics” in a 2D tick and when are they computed?

If enabled (flag or env var), `tick_2d` computes:

* `activePixels`: number of pixels > 0,
* `centroidRow/centroidCol`: value‑weighted center of mass,
* `bbox`: min/max row/col with activity.

It prefers the **furthest downstream `OutputLayer2D`** frame; if that’s all zeros, it falls back to the input frame. Metrics are computed **at the end of the tick** (post‑tick), so they reflect the tick’s full outcome.

---

## Does pruning happen during a tick?

No. **Pruning** is a separate maintenance action you call explicitly (or via a scheduled maintenance pass). During ticks, you only update weights/slots and fire. This keeps event processing fast and predictable.

---

## Are ticks synchronous? Can I batch them?

Ticks are **synchronous**: a call to `tick(...)` or `tick_2d(...)` **runs to completion** (Phase A and Phase B) before the next call starts. You can **loop** over data to simulate a stream. Batching is not required; GrowNet leans into event‑by‑event updates.

---

## Any gotchas when mixing scalar and 2D ticks?

* Bind **different ports** for scalar vs. image inputs.
* For spatial slotting to work, enable it on the **receiving** neurons (e.g., a hidden layer) and provide **2D context** (either via `propagate_from_2d` in Python or deterministic windowed wiring).
* Windowed wiring uses a **center rule** for `"same"` padding (center = floor of midpoint, then clamp to bounds).

---

## How do frozen slots interact with ticks?

A **frozen** slot still **matches and can fire** during Phase A, but it **ignores reinforcement** (and any modulation‑scaled updates). That means post‑tick you still get decay/reset on buses, but the frozen slot’s internal strength/threshold **doesn’t change**, preserving a learned boundary.

---

## How do I know a tick “worked”?

* The region returns **metrics**: `delivered_events` (should be 1 per tick), `totalSlots`, `totalSynapses`, and optional spatial stats.
* You can also inspect layer/frame snapshots (e.g., `OutputLayer2D.get_frame()` in Python) right after the tick.

------

## Can buses simulate dopamine‑like signals?

Yes—very naturally:

- Treat **dopamine bursts** as temporary **gains** on plasticity (`modulationFactor > 1`).
- Treat **dips** as temporary suppression (`modulationFactor < 1`).
- Because modulation **resets each tick**, you get a **phasic** teaching signal.
- Your **frozen slots** ignore these pulses—great for stable anchors.

Optional refinements:

- A **tonic** baseline (slowly drifting multiplier) times a phasic pulse.
- Tiny slot **eligibility traces** so a slightly delayed reward can still reinforce the right slots.

------

## How do I enable spatial slotting in practice?

**Python example**

```python
region = Region("spatial")
l_in  = region.add_input_layer_2d(8, 8, gain=1.0, epsilon_fire=0.01)
l_hid = region.add_layer(excitatory_count=12, inhibitory_count=0, modulatory_count=0)

# Enable spatial focus in the receiving layer
for n in region.get_layers()[l_hid].get_neurons():
    n.slot_cfg.spatial_enabled   = True
    n.slot_cfg.row_bin_width_pct = 50.0
    n.slot_cfg.col_bin_width_pct = 50.0

# Deterministic wiring
region.connect_layers_windowed(l_in, l_hid, kernel_h=3, kernel_w=3, stride_h=2, stride_w=2, padding="valid")

region.bind_input("pixels", [l_in])
m = region.tick_2d("pixels", frame)  # frame = list of rows
```

**C++ parity**: use `Region::connectLayersWindowed(...)` similarly; return is **unique sources**.

------

## How do I freeze/unfreeze a slot?

**Python**

```python
# Freeze the best (or known) slot id on a neuron
n.freeze_slot(slot_id)      # id can be the most active bin you observed
# Later…
n.unfreeze_slot(slot_id)
```

**Java / C++ / Mojo** expose equivalent `freezeSlot(int id)` / `unfreezeSlot(int id)` helpers per neuron.

> Frozen slots still match and can fire, but they **do not** change strength/threshold and **ignore** bus modulation on reinforcement.

------

## What metrics can I inspect per tick?

Core (always on):

- `delivered_events`, `total_slots`, `total_synapses`.

Optional spatial (enable with `Region.enable_spatial_metrics=True` or env `GROWNET_ENABLE_SPATIAL_METRICS=1`):

- `active_pixels` (value > 0),
- `centroid_row`, `centroid_col` (weighted by pixel values),
- `bbox` = `(row_min, row_max, col_min, col_max)`.

Spatial metrics prefer the **furthest downstream** `OutputLayer2D` frame this tick; if that’s all zeros, they fall back to the **input** frame.

------

## Why no pooling layers?

GrowNet isn’t a deep‑learning stack; we avoid hard‑coded pooling to keep the model closer to **event‑driven local learning**. Spatial Focus + windowed wiring already give you **coarse place coding** and **aggregation** without fixed pooling stages.

------

## Does GrowNet support multiple languages? Any parity notes?

- **Python**: reference implementation with Spatial Focus, windowed wiring, demos, tests.
- **C++**: mirrors core features, has deterministic windowed wiring and optional spatial metrics; designed for speed.
- **Mojo**: parity stubs + growing coverage.
- **Java**: production‑friendly structure; uses the slot engine and unified bus decay.

Minor differences may exist (e.g., stricter per‑edge gating in some Java paths vs. immediate fan‑out elsewhere). The codebase tracks these in comments/docs and aims to keep behavior **convergent**.

------

## Troubleshooting: common C++ build errors/warnings

**Error: “invalid use of incomplete type ‘class Neuron’” from `SlotEngine.h`**

- Cause: inline methods in `SlotEngine.h` access `Neuron` members while only a **forward declaration** is visible.
- Fix (pick one):
  1. **Include `Neuron.h`** at the top of `SlotEngine.h` (simple, but watch for cyclic includes), or
  2. **Move** the offending inline bodies into `SlotEngine.cpp` and include `Neuron.h` there.

**Warning: misleading indentation in `Region.cpp` one‑line `if`/`for`**

- Fix: expand one‑liners to blocks:

```cpp
if (r < rmin) { rmin = r; }
if (r > rmax) { rmax = r; }
```

**Linker or missing symbol around `Region::prune` in demos**

- If demos still call `Region::prune(...)` and you don’t use pruning yet, add a **no‑op stub** returning an empty `PruneSummary` so examples compile and run unchanged.

------

## Demos & tests: how do I run them quickly?

**Python demo (spatial focus / moving dot)**

```bash
# from repo root
PYTHONPATH=src/python python src/python/demos/spatial_focus_demo.py
```

**Python tests**

```bash
pytest -q
# Optional spatial metrics:
GROWNET_ENABLE_SPATIAL_METRICS=1 pytest -q
```

**C++ windowed wiring smoke (guarded example)**

```bash
# Example compile (adjust paths/flags to your build)
g++ -std=c++17 -DGROWNET_WINDOWED_WIRING_SMOKE -Isrc/cpp \
    src/cpp/*.cpp src/cpp/tests/WindowedWiringSmoke.cpp -o win_smoke

./win_smoke
```

------

### **Parameter cheat‑sheet for slotting**

- `bin_width_pct` (scalar), `row_bin_width_pct` / `col_bin_width_pct` (2D): width of each delta bin in percent.
- `slot_limit`: maximum number of slots (bins) per neuron; beyond this, a fallback bin is reused to cap growth.
- `epsilon_scale`: lower bound in the denominator to avoid division by zero (set to **1.0** for spatial to prevent oversized bins at the origin).
- `anchor_mode` (2D today): `"FIRST"` (default) or `"ORIGIN"`. (A `"PREVIOUS"` baseline would be a simple extension if/when you want it.)

### Still have questions?

If something feels unclear or you’d like a short example (e.g., dopamine‑like reward loop, frozen‑slot curriculum, or custom 2D binning), add an issue or a note—GrowNet’s design aims to stay **simple, inspectable, and hackable**.