# PR: Finish Temporal Focus TODOs — Mojo parity + small C++ hygiene

You are Codex (GPT-5, max reasoning). Modify all necessary files directly.

## Context
We previously integrated Temporal Focus (anchor-based) across Java/C++/Python and partially in Mojo.
Unfinished work:
- Mojo lacked a reusable, typed, anchor-based selector in `SlotEngine`.
- Mojo `Neuron.on_input(...)` manually reimplemented anchor math (parity risk).
- C++ uses `std::max` in `SlotEngine.cpp`; ensure `<algorithm>` include exists (defensive).

## Targets
- `src/mojo/slot_engine.mojo`
- `src/mojo/neuron.mojo`
- `src/mojo/slot_config.mojo` (verify knobs exist; add if missing)
- `src/cpp/SlotEngine.cpp` (include hygiene only)

## Rules (very important)
- **Mojo:** keep it simple: `struct`, `fn`, explicit param/return types, no clever tricks.
  - Do **not** add `tick_image` in Mojo.
  - Use descriptive variable names (`focus_anchor`, `input_value`, `bin_width_pct`, `epsilon_scale`, `slot_identifier`, etc.).
- **Parity:** math and behavior must match Python’s anchor-first path:
  - `scale = max(abs(focus_anchor), epsilon_scale)`
  - `delta_pct = 100.0 * abs(input_value - focus_anchor) / scale`
  - `slot_identifier = int(delta_pct / max(0.1, bin_width_pct))`
  - Capacity clamp: if `slot_limit >= 0` and `len(slots) >= slot_limit`, clamp to `min(slot_identifier, slot_limit-1)` and ensure the slot exists.
- **Stability:** Do not remove existing public methods. If you refactor, keep a delegating alias.
- **Safety:** Region tick paths must never throw.

## Edits

### 1) Mojo — add a reusable selector to `SlotEngine`
**File:** `src/mojo/slot_engine.mojo`

Add a new function inside `struct SlotEngine`:

```mojo
fn select_anchor_slot_id(
    self,
    focus_anchor: Float64,
    input_value: Float64,
    bin_width_pct: Float64,
    epsilon_scale: Float64
) -> Int:
    var scale: Float64 = focus_anchor
    if scale < 0.0:
        scale = -scale
    if scale < epsilon_scale:
        scale = epsilon_scale
    var delta: Float64 = input_value - focus_anchor
    if delta < 0.0:
        delta = -delta
    let delta_pct: Float64 = 100.0 * delta / scale
    let width: Float64 = if bin_width_pct > 0.1 then bin_width_pct else 0.1
    return Int(delta_pct / width)
```

**Keep** existing `slot_id(...)` (last-input path) unchanged for backwards compatibility.

### 2) Mojo — refactor `Neuron.on_input` to call the new selector
**File:** `src/mojo/neuron.mojo`

Inside `fn on_input(mut self, value: Float64, modulation_factor: Float64) -> Bool:`
- **Keep** the existing state fields (`focus_anchor`, `focus_set`, `focus_lock_until_tick`, `slot_limit`, etc.).
- **Replace** the inline anchor math with a call to `self.slot_engine.select_anchor_slot_id(...)`:
  - Use `focus_anchor` (set it to `value` if `focus_set` is `False`, then set `focus_set = True`).
  - Use default knobs if not present: `bin_width_pct = 10.0`, `epsilon_scale = 1e-6`.
- **Capacity clamp:**
  - If `self.slot_limit >= 0` and `Int(self.slots.size()) >= self.slot_limit`, clamp the computed `slot_identifier` to `self.slot_limit - 1`.
  - Ensure the slot at `slot_identifier` exists after clamping.

Pseudo-structure of the new body (use exact Mojo syntax and types):
```mojo
if not self.focus_set:
    self.focus_anchor = value
    self.focus_set = True

let bin_width_pct: Float64 = 10.0
let epsilon_scale: Float64 = 1e-6
var slot_identifier: Int = self.slot_engine.select_anchor_slot_id(
    self.focus_anchor, value, bin_width_pct, epsilon_scale
)

if not self.slots.contains(slot_identifier):
    if self.slot_limit >= 0 and Int(self.slots.size()) >= self.slot_limit:
        if slot_identifier >= self.slot_limit:
            slot_identifier = self.slot_limit - 1
        if not self.slots.contains(slot_identifier):
            self.slots[slot_identifier] = Weight()
    else:
        self.slots[slot_identifier] = Weight()

var selected_weight = self.slots[slot_identifier]
selected_weight.reinforce(modulation_factor)
let fired: Bool = selected_weight.update_threshold(value)
self.last_fired = fired
self.slots[slot_identifier] = selected_weight
return fired
```

> **Note:** Do **not** reintroduce a `%delta from last_input` path in `on_input`—the anchor-first logic must be the single path for Mojo like Python’s `select_or_create_slot(...)`.

### 3) Mojo — verify `SlotConfig` knobs exist
**File:** `src/mojo/slot_config.mojo`

If any of the following are missing, **add them** inside `struct SlotConfig` with these names/types/defaults:
- `enum AnchorMode: Int: FIRST = 0, EMA = 1, WINDOW = 2, LAST = 3`
- `var anchor_mode: AnchorMode = AnchorMode.FIRST`
- `var bin_width_pct: F64 = 10.0`
- `var epsilon_scale: F64 = 1e-6`
- `var recenter_threshold_pct: F64 = 35.0`
- `var recenter_lock_ticks: Int = 20`
- `var anchor_beta: F64 = 0.05`
- `var outlier_growth_threshold_pct: F64 = 60.0`
- `var slot_limit: Int = 16`

These fields are forward-compat knobs; `on_input` will currently use literals for `bin_width_pct` and `epsilon_scale`, but keeping knobs in the config aligns with other languages.

### 4) C++ — include hygiene for `SlotEngine.cpp`
**File:** `src/cpp/SlotEngine.cpp`

If not present, add:
```cpp
#include <algorithm> // for std::max
```
above or alongside other includes.

## Acceptance checks
- `src/mojo/slot_engine.mojo` contains `fn select_anchor_slot_id(...) -> Int` with exact parameter names and types.
- `src/mojo/neuron.mojo` `on_input` calls `self.slot_engine.select_anchor_slot_id(...)` and enforces capacity clamp exactly once.
- No Mojo `tick_image` is introduced.
- `src/cpp/SlotEngine.cpp` includes `<algorithm>`.
- No public method removed anywhere; behavior matches Python anchor-first logic.

## Output
Print a **single unified diff**. Apply and modify files directly.
