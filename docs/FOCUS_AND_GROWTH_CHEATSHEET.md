# Focus & Growth Cheatsheet (GrowNet)

This is a fast, “operator’s manual” for **Spatial Focus** (2D wiring, bins, tracts) and **Growth** (Slots → Neurons → Layers → Regions).  
It is aligned to the **GrowNet contract**: deterministic behavior, strict slot capacity, two-phase tick discipline, and reproducible growth.

---

## 0) The Golden Rule (one-liner)

> **When the world looks truly new, GrowNet makes room.**  
> Novelty ⇒ new capacity (but bounded + deterministic).

---

## 1) Mental model (what grows, where)

### What “Focus” means
“Focus” is **how input structure is routed** into the network so learning is:
- **Local** (bounded receptive fields)
- **Measurable** (unique-source count)
- **Deterministic** (center mapping, dedupe, recorded rules)

### What “Growth” means
Growth is the system’s escalation ladder:
1. **Slot-level:** allocate a new slot when a new bin appears (if capacity allows).
2. **Neuron-level:** if a neuron repeatedly hits fallback (capacity saturated), grow a new neuron of the **same kind**.
3. **Layer-level:** if the region as a whole is under capacity pressure, add a spillover layer.
4. **Region-level:** (currently mostly pre-allocated) in future, a router/manager can instantiate regions for new domains.

---

## 2) Tick discipline (don’t violate this)

Every tick follows the same discipline:

### Phase A (integrate + select + possibly fire)
- Neuron integrates inputs.
- Chooses / reinforces a slot (strict capacity semantics).
- May fire (emits events).

### Phase B (propagate + observe)
- Events and synapses propagate.
- Demos/tract hooks may observe firings.

### End-tick (state updates)
- Each layer calls `neuron.end_tick()`.
- Then `bus.decay()`:
  - inhibition decays multiplicatively
  - modulation resets to 1.0
  - `current_step += 1` (cooldowns depend on this)

✅ **Invariant:** Growth decisions must respect the tick structure and cooldown logic based on `current_step`.

---

## 3) Slot selection (where “novelty” becomes measurable)

### Anchor mode
- **FIRST**: anchor is fixed on the first observation.

### Scalar binning
- `delta_pct = |x - anchor| / max(|anchor|, epsilon_scale) * 100`
- `bin_width_pct` controls binning granularity.

### 2D binning
- row and col binned separately
- pack `(row_bin, col_bin)` into a deterministic integer key  
  e.g., `key = row_bin * 100000 + col_bin`

### Strict capacity (critical)
- If at capacity, **do not** allocate new slots.
- If a new bin is requested but blocked:
  - reuse a deterministic fallback id
  - set `last_slot_used_fallback = true`

✅ **Invariant:** strict capacity is what makes “pressure” legible and stable.

### Freeze / unfreeze semantics
- `freeze_last_slot()` locks learning on that slot.
- `unfreeze_last_slot()` triggers a **one-shot** preference to reuse that slot next tick:
  - `prefer_last_slot_once = true` (exact naming depends on language; no leading underscores in Python/Mojo)

---

## 4) Focus (2D): windowed wiring, center mapping, dedupe, tracts

GrowNet’s “Spatial Focus” primarily comes from **windowed wiring** in 2D.

### connect_layers_windowed(...)
This builds deterministic connections from a 2D source layer to a 2D target layer.

**Key rules:**
- Each window maps to its **center** target index.
- Each source pixel connects according to those windows.
- **Duplicates are deduped** (a source can appear in multiple windows; it should not create duplicate edges).

✅ **Return value invariant:**  
`connect_layers_windowed(...)` returns the **unique source count** that participated in ≥ 1 window.

### SAME vs VALID (conceptually)
- **SAME**: output grid size matches input; padding implied.
- **VALID**: no padding; only fully valid windows.

### Center rule (canonical)
Centers are derived by floor semantics + clamp to valid target indices.

> Think: “each window chooses its **center target**; sources within that window feed that center.”

### Tracts (windowed wiring representation)
In windowed wiring, you typically build a **Tract** (explicit wiring structure).

When a **source neuron grows**, windowed wiring must re-attach deterministically:

✅ `Tract.attachSourceNeuron(new_index)` must be called so the new source neuron is connected in the same windowed pattern.

### OutputLayer2D center mapping nuance
For OutputLayer2D, each sliding window maps to the **center** target index (not the corner).

---

## 5) Growth ladder: triggers and actions

### 5.1 Slot → Neuron (neuron growth)
**Trigger:**
- neuron is at strict slot capacity AND
- fallback used in consecutive inputs ≥ `fallback_growth_threshold` AND
- ticks since last neuron growth ≥ `neuron_growth_cooldown_ticks`

**Action:**
- layer adds **one neuron of the same kind** as the seed neuron
- copy slot config + slot limit
- share bus / copy bus reference (per language design)
- set `owner` backref where required
- deterministic autowiring (see next section)

✅ **Goal:** “fallback streak” means the neuron is overloaded by novelty → grow.

---

### 5.2 Neuron → Layer (region growth)
**Triggers (OR):**
- region average slots/neuron ≥ `avg_slots_threshold` OR
- percent(neurons at capacity AND using fallback) ≥ `percent_at_cap_fallback_threshold`

**Rules:**
- **one growth per region per tick**
- respect `max_layers` and `layer_cooldown_ticks`

**Action:**
- add a small spillover layer (often excitatory-only)
- connect saturated → new **with p=1.0** (deterministic spillover topology)
- use region RNG for reproducibility when randomness is allowed

✅ **Invariant:** `request_layer_growth` uses `p=1.0` unless a policy explicitly overrides.

---

### 5.3 Layer → Region (dynamic regions)
Today: regions are mostly **pre-allocated** (hyperparameter: how many initial regions).  
Future: region creation should be handled by a top-level `RegionManager/Router` under:
- clear novelty trigger across existing regions
- cooldown + budget
- deterministic wiring rules

---

## 6) Deterministic autowiring (mesh rules + windowed tracts)

### Mesh rules
Whenever `connect_layers(src, dst, p, feedback)` is called:
- record a **mesh rule** so growth can replay wiring deterministically.

When a neuron grows in a layer:
- outbound: new source → each recorded dst layer with recorded p
- inbound: each recorded src layer → new target with recorded p

### Windowed tracts
`connect_layers_windowed(...)` creates explicit tract structures.
When a source neuron grows:
- `tract.attach_source_neuron(new_idx)` must be called

✅ **Invariant:** new neurons must “inherit” the same connectivity patterns deterministically.

---

## 7) Optional: Proximity connectivity policy (sidecar)

Purpose: deterministic adjacency wiring based on geometric proximity in a fixed layout.

**Timing:** once per tick after Phase‑B and before end_tick/decay.  
**Search:** spatial hash buckets; verify Euclidean distance ≤ radius.  
**Probability:** STEP / LINEAR / LOGISTIC (probabilistic modes use Region RNG).  
**Guards:** per‑tick max edges; per‑source cooldown; per‑region once-per-step guard.

✅ **Policy is additive:** no core mutation beyond calling existing connect APIs.

---

## 8) Key knobs (defaults + what they do)

### SlotConfig defaults (commonly)
- `growth_enabled = true`
- `neuron_growth_enabled = true`
- `layer_growth_enabled = false` (opt-in)
- `fallback_growth_threshold = 3`
- `neuron_growth_cooldown_ticks = 0`

### Region growth policy knobs
- `avg_slots_threshold` (domain-specific)
- `percent_at_cap_fallback_threshold` (0.0 disables OR path)
- `max_layers`
- `layer_cooldown_ticks`

### Focus knobs (2D)
- kernel size `(kernel_h, kernel_w)`
- stride `(stride_h, stride_w)`
- padding: `"same"` or `"valid"`
- dedupe semantics (must remain enabled)

### Determinism knobs
- stable RNG seeding (use region RNG only)
- PAL ordered reduction
- stable tiling
- no global randomness

---

## 9) Metrics & signals (debug checklist)

If something “isn’t growing” or “grows too much”, inspect:

### Slot-level
- `last_slot_used_fallback` (is fallback actually happening?)
- slot count vs capacity
- anchor value (is FIRST anchor reasonable?)

### Neuron-level
- `fallback_streak`
- `last_neuron_growth_step`
- cooldown ticks
- “same kind” growth (did it grow the correct neuron type?)

### Region-level
- average slots/neuron
- percent at-capacity + fallback
- `last_layer_growth_step`
- `max_layers`

### Focus wiring
- unique source count returned by `connect_layers_windowed`
- tract attach calls on growth
- center mapping correctness for SAME/VALID

### System-level invariants
- one growth per region per tick
- bus decay increments step (cooldowns depend on it)
- PAL determinism holds across worker counts (where applicable)

---

## 10) Sanity scenarios (quick tests you can run mentally)

### A) Repeated identical input
- slot selection should stabilize (same slot repeatedly)
- no fallback
- no growth

### B) Alternating bins beyond slot capacity
- fallback should start occurring
- fallback streak should rise
- neuron growth should occur after threshold (and cooldown)
- new neuron should be auto-wired deterministically

### C) Region saturation
- many neurons at capacity + fallback
- region growth policy triggers (OR)
- new layer added
- deterministic spillover connections with `p=1.0`

---

## 11) Common pitfalls (what breaks parity)

- Returning “edge count” instead of **unique source count** for windowed wiring
- Missing dedupe in 2D wiring
- Not calling `attach_source_neuron` on source growth (tract parity break)
- Using global RNG instead of Region RNG
- Violating tick discipline (growth inside the wrong phase)
- Forgetting `bus.decay()` step increment (cooldowns break)
- Allowing >1 region growth per tick
- Using leading underscores in Python/Mojo identifiers (style rule)

---

## 12) Naming & style reminders (cross-language)

- Python & Mojo: **no leading underscores** in identifiers.
- Java & C++ public APIs: camelCase / PascalCase only.
- Avoid 1–2 character variable names (except `i`, `j` loop indices).
- Keep growth wiring deterministic; prefer `p=1.0` for spillover unless policy says otherwise.

---

## 13) One-sentence “focus + growth” summary

**Focus** controls how signals are spatially routed (windowed, center-mapped, deduped, tract-tracked).  
**Growth** controls how capacity expands under novelty pressure (fallback streak + cooldown ⇒ new slots/neurons/layers, deterministically auto-wired).