Totally—here’s the clear, no-mystery version of **when and why GrowNet grows**. Think of growth as a small, sensible ladder: **Slots → Neurons → Layers → Region**. We always try to grow the **smallest** thing that lets learning continue, and we only do it when a simple “pressure” signal says “I’m full but new stuff is still showing up.”

------

## The one idea behind all growth

> **Pressure = “I wanted a new bin but I couldn’t.”**

Every time a neuron receives input it tries to choose a **slot** (a bin).

- If the desired bin already exists → it uses it.
- If it doesn’t exist **and** the neuron still has capacity → it creates it.
- If it **doesn’t have capacity** (already at `slot_limit`) or the desired bin is **out of range**, it **reuses a fallback slot** and sets a flag: **`last_slot_used_fallback = true`**.

That single flag is the signal for all growth above slots.

------

## 1) Slot growth (inside a neuron)

**Condition to grow a slot**

- Desired bin **does not exist**, **and** the neuron is **below** its `slot_limit`.
- Action: create the slot (the “drawer” doesn’t exist yet and there’s room for it).

**When slot growth is blocked**

- The neuron is **at** `slot_limit` (or the desired bin is out of domain).
- Action: **do not create** a slot; reuse a deterministic fallback slot and mark `last_slot_used_fallback = true`.
   This tells us: “I’m full, but novelty is still arriving.”

> In 2D, “desired bin” is the pair `(row_bin, col_bin)`. Same rules apply.

------

## 2) Neuron growth (within a layer)

**Why do we grow a neuron?**
 Because one neuron’s slots keep getting “novelty pressure” (fallback reuse) even though it’s full.

**Conditions (all must be true)**

1. The neuron is **at capacity** (`slot_count >= slot_limit`).
2. On this tick, **`last_slot_used_fallback == true`** (it wanted a new bin but re-used fallback).
3. This has happened for **N consecutive times** (the **fallback streak** ≥ `fallback_growth_threshold`, e.g., 3).
4. **Cooldown** has elapsed: `(bus.current_step - last_growth_tick) ≥ neuron_growth_cooldown_ticks`.
   - `bus.current_step` increments **once per tick** during decay; that’s your clock.

**Action**

- Ask the **owner layer** to **add a neuron of the same kind** (E/I/M), carrying over the slot policy and limit.
- Region then **auto-wires** this new neuron **deterministically**:
  - **Mesh edges:** replay saved wiring rules (probabilities and feedback flags).
  - **Windowed tracts (2D):** re-attach the new source neuron so it feeds the same windows as its peers.

**After effect**

- Reset that neuron’s fallback streak.
- Update its `last_growth_tick` with the current bus step (so cooldown starts).

------

## 3) Layer growth (adding a new layer in the region)

There are **two** practical paths to a new layer:

### A) **Escalation from the layer** (neuron growth is blocked)

- A neuron requests growth, **but the layer has reached its `neuron_limit`**.
- If `layer_growth_enabled` is true, the layer asks the **Region** to create a **spillover layer**.

**Action**

- Region adds a **small, excitatory-only** spillover layer and wires **saturated → new** with **probability = 1.0** (deterministic).
- Auto-wiring uses the same seed/RNG so you can reproduce topology.

### B) **Region policy at end-of-tick** (global pressure)

- Even if layers haven’t hit their caps, the region can decide to add a layer when the overall system is pushing against capacity.

**Conditions (any of these triggers, plus cooldown)**

- **Average slots per neuron** ≥ `avg_slots_threshold` (e.g., many neurons are nearly full).
- **Percentage of neurons at capacity & using fallback** ≥ `percent_at_cap_threshold` (e.g., 50%).
- **Cooldown** passed: `(region_bus.current_step - last_region_growth_step) ≥ layer_cooldown_ticks`.
- **Max layers** not exceeded.
- **One growth per tick**: Region grows at most **one** layer each tick.

**Action**

- Choose the **most saturated** layer as the donor (or your chosen heuristic).
- Create a spillover layer; wire **donor → new** with **p = 1.0** for determinism; optionally duplicate inbound mesh rules if you want symmetric wiring.
- Record the event (so tests and demos can assert “one growth this tick”).

------

## 4) Region growth (automatic, whole-region viewpoint)

This is simply the **B path** above: the Region looks at the **big picture** at end-of-tick:

**Conditions**

- **Pressure:** average slots per neuron **or** `% of neurons at cap with fallback`.
- **Cooldown** and **max layers** respected.
- **One growth per tick** guaranteed.

**Action**

- Add **one** layer; wire deterministically; update metrics.

------

## 5) Cooldowns and clock (how time is measured)

- Each **LateralBus/RegionBus** increases a **`current_step`** by **1** during **decay** (end-of-tick).
- All cooldowns compare “last growth step” vs. `current_step`.
- That’s it—no wall clock, no timeouts, just ticks.

------

## 6) What **doesn’t** cause growth (common confusions)

- A **single** fallback event does **not** grow a neuron—only a **streak** of fallback events at capacity does.
- If **growth is disabled** (`growth_enabled=False` or `neuron_growth_enabled=False`), no neuron growth occurs even if fallbacks happen.
- If **`slot_limit` is high enough** (or `-1`), slots will keep growing and neuron growth will not trigger.
- Input neurons (in Input layers) **don’t** typically trigger growth requests; they’re just ingress points. (We still set `owner` for consistency.)

------

## 7) Wiring after growth (why behavior stays stable)

- **Mesh rules** are recorded whenever you call `connect_layers`. On neuron/layer growth, those rules are **replayed** to wire the new parts with the **same probabilities** and feedback flags, using a **seeded RNG** for reproducibility.
- **Windowed (2D)** tracts are stored as tract objects. When a **source layer** grows, the tract **attaches** the new source neuron so it immediately starts delivering to the same “center” outputs as its peers.
- For **spillover layers**, we standardize on **p = 1.0** from **donor → new** so the new layer becomes a clearly defined continuation path (and simple to debug).

------

## 8) Defaults (you can start with these)

- `slot_limit = 16` (per neuron)
- `bin_width_pct = 10.0` (scalar), `row/col_bin_width_pct = 10.0` (2D)
- `growth_enabled = True`
- `neuron_growth_enabled = True`
- `fallback_growth_threshold = 3`
- `neuron_growth_cooldown_ticks = 0` (good for experiments; raise it in long runs)
- Region growth: `avg_slots_threshold ≈ 12.0`, `% at cap threshold ≈ 50%`, `layer_cooldown_ticks = 20`, `spillover wire probability = 1.0`

------

## 9) A 10-second mental model

- **Slot phase**: “Can I open a new drawer?” If yes, do it. If not, **reuse** a drawer and wave the **fallback** flag.
- **Neuron phase**: “Have I been waving the fallback flag **for several ticks** while full?” If yes (and cooldown ok), **add a neuron like me**, then wire it like my peers.
- **Layer phase**: “Is my layer full of neurons and a growth request arrived?” If policy allows, ask the **Region** to create a **spillover layer** and wire it.
- **Region phase**: “Is the whole system pressing against its limits?” If yes (and cooldown ok), add **one** spillover layer and wire it **deterministically**.

That’s all. If you remember **“fallback streak at capacity”** and **“one growth per tick”**, you’ll always be able to reason about what should happen next.

------

If you want, I can generate a **one-page cheatsheet** with these conditions and the common knobs so you can keep it next to your IDE.