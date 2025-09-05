Great question. In GrowNet, a **cooldown** is simply a short “quiet period,” measured in **ticks**, that must pass **between growth events** so the system doesn’t thrash. It’s how we give the network time to **use** the capacity it just added before deciding to grow again.

Below is a clear, practical breakdown.

------

## What a cooldown actually is

- A **cooldown** is a **minimum number of ticks** that must pass **after a growth event** before the same entity is allowed to grow again.
- Cooldowns are checked using the buses’ **`current_step`** counter, which is incremented **once** at the end of each tick (during bus decay). No wall-clock time is involved.

Think of it like a “refractory period” for growth: *learn with what you have for a bit, then reconsider growing*.

------

## Where cooldowns are used

### 1) Neuron growth cooldown (per-neuron)

- **Why:** prevent a single neuron from spawning a burst of siblings in consecutive ticks.
- **State:** each neuron stores `last_growth_tick`.
- **Knob:** `neuron_growth_cooldown_ticks` (in the neuron’s `slot_cfg`).
- **Check (per tick):**
  - Neuron is **at slot capacity**.
  - The **fallback flag** (wanted a new bin but couldn’t) is set.
  - The **fallback streak** ≥ `fallback_growth_threshold`.
  - **Cooldown passed:**
     `bus.current_step - last_growth_tick ≥ neuron_growth_cooldown_ticks`
- **Action:** call `owner_layer.try_grow_neuron(seed)`, set `last_growth_tick = bus.current_step`.

### 2) Layer growth cooldown (via Region policy)

- **Why:** once the layer is saturated and asks Region for a **spillover layer**, give the whole region time to settle before adding more.
- **State:** region stores `last_region_growth_step` (or equivalent).
- **Knob:** `layer_cooldown_ticks` (in Region growth policy).
- **Check (end-of-tick):**
  - **Pressure** trigger(s) satisfied (e.g., average slots per neuron ≥ threshold **or** % of neurons at cap & fallback ≥ threshold).
  - **Cooldown passed:**
     `region_bus.current_step - last_region_growth_step ≥ layer_cooldown_ticks`
  - **One growth per tick** guard.
- **Action:** add one spillover layer, wire deterministically (default **p = 1.0**), set `last_region_growth_step = current_step`.

> You can have **both** neuron cooldown and layer cooldown active; they operate at **different scopes** and do not conflict.

------

## Why cooldowns matter

- **Stability:** After growth, activity redistributes. Without a cooldown, you might “double-count” the same transient pressure and over-grow.
- **Signal quality:** Gives the network time to “prove” that the newly added capacity absorbed the novelty pressure.
- **Determinism & testability:** Keeps growth decisions sparse and predictable.

------

## The math boiled down

### Neuron cooldown (checked in neuron’s on-input path)

```
if at_capacity and last_slot_used_fallback:
    fallback_streak += 1
else:
    fallback_streak = 0

if fallback_streak >= fallback_growth_threshold:
    if (bus.current_step - last_growth_tick) >= neuron_growth_cooldown_ticks:
        owner_layer.try_grow_neuron(self)
        last_growth_tick = bus.current_step
    fallback_streak = 0
```

### Region (layer) cooldown (checked at end-of-tick)

```
if pressure >= threshold and (region_step - last_region_growth_step) >= layer_cooldown_ticks:
    request_layer_growth(saturated_layer)
    last_region_growth_step = region_step
# enforce one-growth-per-tick separately
```

> **Pressure** can be defined as *avg slots per neuron* or *% of neurons at capacity with fallback* (we support either/or).

------

## Tuning guidance (good starting points)

- **Exploration / lab runs:**
   `neuron_growth_cooldown_ticks = 0–2` (reactive), `layer_cooldown_ticks = 5–20`.
- **Stability / long runs:**
   `neuron_growth_cooldown_ticks = 10–30`, `layer_cooldown_ticks = 20–50`.
- **Aggressive demos:**
   Lower both to showcase growth quickly (but expect more volatility).

**Rule of thumb:** If you observe “stair-step” overgrowth, **raise cooldowns** (and/or raise the fallback streak threshold). If growth feels stuck even though you see many fallbacks at capacity, **lower cooldowns** slightly.

------

## Common pitfalls (and how to avoid them)

- **Forgetting the clock:**
   Ensure `bus.decay()` increments `current_step` **exactly once** per tick (in every language). If it doesn’t move, cooldowns never expire.
- **Zero cooldown + low threshold = thrash:**
   You might spawn multiple neurons across consecutive ticks before the new one has any effect. Start with a small cooldown.
- **Cooldown too high:**
   Growth appears “stuck” for long stretches even under clear pressure. Lower it gradually.
- **Using wall-clock time:**
   Cooldowns are **tick-based**. Wall-clock pauses won’t affect them (by design).

------

## How it interacts with frozen slots

Frozen slots only block **learning updates** inside the slot (reinforcement/threshold change). They do **not** suppress fallback marking or cooldown logic. So you can freeze a slot to protect its value while still letting the **growth** system respond to novelty pressure in other bins.

------

## Quick example

- Neuron has `slot_limit = 1`, `fallback_growth_threshold = 2`, `neuron_growth_cooldown_ticks = 3`.
- Ticks 100–101: desired bins are new but blocked → fallback set both ticks → streak = 2.
- Tick 101 end:
   `current_step - last_growth_tick (=-1) = 102` ≥ 3 → **grow a neuron**; set `last_growth_tick = 101`.
- Ticks 102–103: Even if fallback continues, growth is **suppressed** until step ≥ 104.

------

## In one sentence

> A **cooldown** is a *tick-based wait* that must elapse after a growth event—per neuron or per region—so growth decisions are stable, testable, and meaningful.

If you want, I can generate a tiny **“cooldown dashboard”** patch (per-tick counters + log line) so you can watch cooldown timers and growth decisions during demos.