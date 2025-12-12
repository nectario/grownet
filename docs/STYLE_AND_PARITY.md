# STYLE & PARITY — Rules Codex must enforce

This document is a **high‑signal checklist** for keeping GrowNet consistent across languages.

## Source of truth

1. **GrowNet_Contract_v5_master.yaml** — public APIs + invariants
2. **GrowNet_Design_Spec_V5.md** — behavioral details (growth, tick phases, wiring)
3. **CODING_STYLE_MUST_READ.md** — naming + clean code + determinism rules

If any file contradicts the contract/spec, **fix or archive it**.

---

## Language conventions (public API + naming)

- **Python**
  - `snake_case`
  - **No leading underscores** in public APIs or fields
- **Mojo**
  - `struct` + `fn`
  - parameters/returns are typed
  - **No leading underscores** in public APIs or fields
- **Java**
  - `camelCase` public APIs; `PascalCase` types
- **C++**
  - Public header APIs are `camelCase` / `PascalCase` (no snake_case in public headers)
- **TypeScript**
  - `camelCase` public APIs; `PascalCase` types
- **Rust**
  - idiomatic `snake_case` for functions/fields, `PascalCase` types
  - public APIs must remain descriptive (avoid abbreviations)

**Across all languages:**
- Use **descriptive identifiers** (avoid single/double‑character names; `i/j` loop indices are ok).
- Deterministic seeds/ordering where randomness exists (no ambient/global randomness).

---

## Core behavioral parity (must match everywhere)

These are the invariants that every implementation must satisfy:

- **Two‑phase tick discipline**
  - Phase A: integrate input, pick/reinforce slot, maybe fire
  - Phase B: propagate events
  - End tick: `neuron.end_tick()` then `bus.decay()`

- **Strict slot capacity + fallback**
  - Once a neuron hits `slot_limit`, **no new slot is allocated**
  - When a new bin is desired but blocked, reuse deterministic fallback ID and set:
    - `last_slot_used_fallback = true`

- **Freeze / unfreeze semantics**
  - `freeze_last_slot()` locks learning on that slot
  - `unfreeze_last_slot()` triggers a one‑shot preference to reuse the frozen slot next tick
    - Python/Mojo name: `prefer_last_slot_once`
    - Java/C++/TS name: `preferLastSlotOnce`

- **Neuron growth**
  - Trigger: fallback streak ≥ `fallback_growth_threshold` AND cooldown satisfied
  - Action: add **one neuron of the same kind**; copy slot config/limits; set owner backrefs where needed
  - Autowiring is deterministic via recorded mesh rules / tracts

- **Layer growth (region policy)**
  - Trigger uses OR logic: `avg_slots_threshold` **or** `% at‑cap + fallback`
  - Enforce **≤ 1 growth action per region per tick**
  - Spillover wiring uses **p = 1.0** (unless an explicit policy overrides)

- **Windowed wiring (2D)**
  - SAME/VALID semantics with **center mapping**
  - Dedupe duplicate edges across overlapping windows
  - Return value is **unique source count**
  - On source growth, windowed tracts must re‑attach deterministically via:
    - `attach_source_neuron(new_src)` / `attachSourceNeuron(newSrc)`

---

## Buses (LateralBus / RegionBus)

Bus behavior must be identical across languages:

- **Inhibition decays multiplicatively** each tick (e.g., `inhibition *= 0.90` when decay is 0.90)
- **Modulation resets** to `1.0` each tick
- **Step counter increments** each tick (`current_step` / `currentStep += 1`) — cooldown logic depends on this

Tests should be able to assert something like:

- `expected_inhibition = initial_inhibition * decay_factor` after one `decay()` call

---

## Practical guidance for Codex

When making changes:

- Prefer updating **contract/spec‑aligned docs** over adding new free‑form notes.
- If a doc is outdated, move it to `docs/archive/` and leave a short pointer in the active doc if needed.
- Never “fix” parity by changing only one language; parity changes must be applied across all languages (or explicitly documented as pending).

