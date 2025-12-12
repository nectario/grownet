This is a tight, one-page **Growth & Focus Cheatsheet**

------

# GrowNet — Growth & Focus Cheatsheet (1-pager)

**Mental model:** GrowNet always tries to grow the **smallest** thing that keeps learning going — **Slots → Neurons → Layers → Region**. The single pressure signal is:

> **“I wanted a new bin but I couldn’t.”** → `last_slot_used_fallback = true`

------

## A) Two-phase tick (the clock)

- **Phase A — Deliver/Fire:** inputs → slot selection (FIRST anchor), reinforce, threshold, fire + propagate.
- **Phase B — End-of-tick/Decay:** `layer.end_tick()` then `bus.decay()`
  - **Inhibition** *= `decay_rate` (e.g., 0.90)
  - **Modulation** = **1.0**
  - **current_step += 1** (tick clock)
- All cooldowns use **`current_step`** (ticks), not wall-clock.

------

## B) Focus & Slotting (strict capacity)

**Scalar (Temporal Focus, FIRST anchor)**

```
scale     = max(|anchor|, epsilon_scale)
delta_pct = 100 * |x - anchor| / scale
slot_id   = floor(delta_pct / bin_width_pct)
```

- If `slot_count < slot_limit` and slot_id not present → **create** slot.
- If **at capacity** or out-of-domain → **reuse deterministic fallback** (never create) and set:
  - `last_slot_used_fallback = true`

**2D (Spatial bins)** — same rules; slot key is `(row_bin, col_bin)` (packed).

**Frozen slots**

- `freeze_last_slot()` → no reinforce/threshold updates for that slot.
- `unfreeze_last_slot()` → unfreeze and **prefer that slot once** on the next tick.

------

## C) Growth ladder (conditions & actions)

### 1) Slot growth (inside a neuron)

- **Condition:** desired bin not present **AND** `slot_count < slot_limit`.
- **Action:** create the slot.

### 2) Neuron growth (inside a layer)

**Trigger (all required):**

1. Neuron **at capacity** (`slot_count ≥ slot_limit`)
2. On this tick, **`last_slot_used_fallback == true`**
3. **Streak:** consecutive fallbacks ≥ `fallback_growth_threshold`
4. **Cooldown:** `(bus.current_step - last_growth_tick) ≥ neuron_growth_cooldown_ticks`

**Action:** `owner_layer.try_grow_neuron(seed)`

- Create neuron of the **same kind** (E/I/M), copy slot policy & limit, attach to same bus.
- **Autowire** deterministically:
  - **Mesh rules:** replay outbound + inbound probabilities
  - **Windowed tracts (2D):** re-attach new source via `attachSourceNeuron(new_index)`
- Reset streak; set `last_growth_tick = current_step`.

### 3) Layer growth (ask Region for spillover)

- **When:** layer is at **neuron_limit** and neuron growth was requested; policy allows.
- **Action:** Region creates a small **spillover** layer; wire **donor → new with probability = 1.0** (deterministic).
   *(Optionally duplicate inbound rules if desired.)*

### 4) Region growth (policy-driven, end-of-tick only)

**Trigger (cooldown + one per tick):**

- `average_slots_per_neuron ≥ avg_slots_threshold` **OR**
- `% of neurons at capacity & fallback ≥ percent_at_cap_threshold`
- `(region_step - last_region_growth_step) ≥ layer_cooldown_ticks`

**Action:** grow **ONE** layer; wire deterministically (default p = **1.0**); update `last_region_growth_step`.

------

## D) Windowed (tract) wiring — quick rules

- **`connect_layers_windowed(src2D, dst, kernel, stride, padding)`**
- **Return value:** number of **unique source subscriptions** (distinct source pixels participating in ≥1 window)
- **Center rule (OutputLayer2D):** window center = `r0 + kh//2`, `c0 + kw//2` (floor + clamp to bounds)
   Each participating source connects to **that** center output neuron (dedup `(src,center)`).
- **Generic dest:** first time a source participates, connect it to **all** dest neurons (deterministic fan-out).
- **Growth:** when the **source layer** grows a neuron, the tract **re-attaches** to include it.

------

## E) Knobs (defaults & where to tweak)

**Per-neuron (`SlotConfig` or equivalent)**

- `slot_limit` = **16** (`-1` = unlimited)
- `bin_width_pct` = **10.0**, `epsilon_scale` = **1e-6**
- `growth_enabled` = **True**
- `neuron_growth_enabled` = **True**
- `fallback_growth_threshold` = **3**
- `neuron_growth_cooldown_ticks` = **0–10** (0 for demos, higher for stability)
- `layer_growth_enabled` = **False** (escalation allowed; Region policy still decides)

**Region policy**

- `enable_layer_growth` = True/False
- `avg_slots_threshold` ≈ **12.0** (with limit 16)
- `percent_at_cap_threshold` ≈ **50%**
- `layer_cooldown_ticks` = **20** (start here; tune up/down)
- `max_layers` = cap as needed
- `rng_seed` = **1234** (or your standard)
- `spillover_wire_probability` = **1.0** (deterministic)

**Bus decay**

- Inhibition *= `decay_rate` (e.g., **0.90**)
- Modulation = **1.0**
- `current_step += 1` (tick clock)

------

## F) Quick sanity checks (your “is it healthy?” list)

- **Strict capacity:** `len(neuron.slots)` never exceeds `slot_limit` (except empty bootstrap).
- **Fallback signal:** `last_slot_used_fallback` flips **true** whenever capacity blocks a new bin (scalar & 2D).
- **One growth per tick:** region grows **≤ 1** layer per tick.
- **Cooldown effect:** growth events for the same neuron/layer are **≥ cooldown** ticks apart.
- **Windowed wiring:** `connect_layers_windowed(... )` returns the expected **unique sources**; center rule matches floor+clamp.

------

## G) Tuning cheats

- **Too aggressive growth?** ↑ `fallback_growth_threshold` or ↑ cooldowns.
- **Growth seems stuck?** ↓ cooldowns slightly or ↓ thresholds.
- **Noisy 2D wiring?** Keep spillover **p=1.0** for clarity; adjust mesh probabilities elsewhere.
- **Need stable demos/tests?** Fix `rng_seed`; keep spillover deterministic.

------

**That’s it — 95% of the time you only need to watch**
 `last_slot_used_fallback`, `fallback_streak`, `current_step`, and “one growth per tick.”