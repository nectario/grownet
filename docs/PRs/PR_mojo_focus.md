
# PR: Mojo temporal focus (anchor-first) + V4 docs

You are Codex (GPT-5 Pro, max reasoning). Apply the following *surgical*, idempotent edits directly to the working tree.

## Scope
- **Mojo**: add temporal focus knobs to `slot_config.mojo`, add an anchor-slot helper to `slot_engine.mojo`, and make `neuron.mojo`’s `on_input` use anchor-first selection with capacity clamping—no clever tricks, fully typed, descriptive names.
- Do **not** change Java/Python/C++ files in this PR.

## Guardrails
- Keep changes **idempotent** (if code already exists, do nothing).
- Do **not** remove public methods. If behavior changes, keep signatures as-is.
- Mojo style: use `struct`, `fn`, explicit types; avoid fancy constructs; use clear names.

---

## 1) Mojo: add anchor/focus knobs to `src/mojo/slot_config.mojo`

**Precheck**: file exists and contains `struct SlotConfig:` and policy aliases (`SLOT_FIXED`, etc.).

**Edit (idempotent)**: Inside `struct SlotConfig:` (after the existing policy fields), ensure the following block exists. If it already exists (detected by `anchor_mode` or `ANCHOR_FIRST` symbols), skip insertion.

```mojo
    # --- Temporal Focus (anchor-based) knobs ---
    # Anchor modes (simple integer aliases to stay compiler-friendly)
    alias ANCHOR_FIRST:  Int64 = 0
    alias ANCHOR_EMA:    Int64 = 1
    alias ANCHOR_WINDOW: Int64 = 2
    alias ANCHOR_LAST:   Int64 = 3

    var anchor_mode:                  Int64 = ANCHOR_FIRST
    var bin_width_pct:                F64   = 10.0
    var epsilon_scale:                F64   = 1e-6
    var recenter_threshold_pct:       F64   = 35.0
    var recenter_lock_ticks:          Int64 = 20
    var anchor_beta:                  F64   = 0.05
    var outlier_growth_threshold_pct: F64   = 60.0
    var slot_limit:                   Int64 = 16
~~~

**Notes**

- We intentionally use integer aliases (like existing `SLOT_FIXED`) instead of `enum` to avoid syntax drift across Mojo versions.
- This aligns names with Python/Java (`bin_width_pct`, `epsilon_scale`, `slot_limit`, etc.).

------

## 2) Mojo: add anchor-slot helper to `src/mojo/slot_engine.mojo`

**Precheck**: file exists with `struct SlotEngine:` and `fn slot_id(...)`.

**Edit (idempotent)**: Add a *pure* helper that computes an anchor-based slot id without referencing `Neuron` or `Weight`. Skip if a function with the same signature already exists.

```mojo
    fn anchor_slot_id(
        self,
        focus_anchor: Float64,
        input_value: Float64,
        bin_width_pct: Float64,
        epsilon_scale: Float64
    ) -> Int:
        # Compute |Δ%| relative to anchor, map to non-negative bucket id.
        var scale: Float64 = focus_anchor
        if scale < 0.0:
            scale = -scale
        if scale < epsilon_scale:
            scale = epsilon_scale

        var delta_value: Float64 = input_value - focus_anchor
        if delta_value < 0.0:
            delta_value = -delta_value

        let delta_percent = 100.0 * (delta_value / scale)
        let width = if bin_width_pct > 0.1 then bin_width_pct else 0.1
        let slot_identifier: Int = Int(delta_percent / width)
        return slot_identifier
```

**Notes**

- This avoids circular imports (`Neuron` <-> `SlotEngine`) and keeps `SlotEngine` a utility for slot math (parity with Python `slot_engine` behavior).

------

## 3) Mojo: use anchor-first selection in `src/mojo/neuron.mojo`

**Precheck**: file exists with `struct Neuron:` and a method `fn on_input(`. Also confirm presence of focus fields (`focus_anchor`, `focus_set`, `focus_lock_until_tick`). If missing, add them once under the existing state vars.

```mojo
    # If these fields are absent, insert them once (idempotent)
    var focus_anchor: Float64 = 0.0
    var focus_set:    Bool    = False
    var focus_lock_until_tick: Int = 0
```

**Replace body of `fn on_input(...)` (idempotent)**:

- Find the implementation of `fn on_input(mut self, value: Float64, modulation_factor: Float64) -> Bool`.
- Replace the *slot selection* part with anchor-first semantics using `self.slot_engine.anchor_slot_id(...)`.
- Keep the same signature and reinforcement/threshold update logic; preserve the final return bool.

**New body template** (clamp capacity using `self.slot_limit`; create `Weight` if needed):

```mojo
    fn on_input(mut self, value: Float64, modulation_factor: Float64) -> Bool:
        # --- Anchor-first temporal focus ---
        if not self.focus_set:
            self.focus_anchor = value
            self.focus_set = True

        # Compute anchor-based slot id (defaults: 10% bins, 1e-6 epsilon)
        let computed_slot_id = self.slot_engine.anchor_slot_id(
            self.focus_anchor, value, 10.0, 1e-6
        )
        var slot_id: Int = computed_slot_id

        # Ensure slot exists with capacity clamp
        if not self.slots.contains(slot_id):
            if self.slot_limit >= 0 and Int(self.slots.size()) >= self.slot_limit:
                # clamp into range [0, slot_limit-1]
                if slot_id >= self.slot_limit:
                    slot_id = self.slot_limit - 1
                if not self.slots.contains(slot_id):
                    self.slots[slot_id] = Weight()
            else:
                self.slots[slot_id] = Weight()

        var slot = self.slots[slot_id]

        # Reinforcement + threshold update (existing semantics)
        slot.reinforce(modulation_factor)
        let fired = slot.update_threshold(value)

        self.last_fired = fired
        self.slots[slot_id] = slot  # writeback
        return fired
```

**Notes**

- We deliberately **do not** depend on `SlotConfig` in Mojo yet to avoid cascading changes; anchor bin width & epsilon use stable defaults (`10%`, `1e-6`). This mirrors Python’s default behavior.
- If you later thread `SlotConfig` through Mojo, this body can read `bin_width_pct`, `epsilon_scale`, and `slot_limit` from that instance instead of constants / `self.slot_limit`.

------

## 4) Postconditions (verify)

After edits, run these checks. If any fails, stop and report what failed.

- Mojo symbols:
  - `rg -n "anchor_mode|ANCHOR_FIRST|slot_limit" src/mojo/slot_config.mojo`
  - `rg -n "anchor_slot_id\\(" src/mojo/slot_engine.mojo`
  - `rg -n "focus_anchor|focus_set" src/mojo/neuron.mojo`
  - `rg -n "anchor_slot_id\\(" src/mojo/neuron.mojo`

**If all checks pass**, print a short summary like:

```
Mojo: slot_config (+focus knobs), slot_engine (+anchor_slot_id), neuron (anchor-first selection) — OK
```

**If any check fails**, print the failing command(s) and the reason.

------

## Output Formatting

- Make the edits directly (no separate `codex apply`).
- Print the short success summary or precise failure logs only.

```
---

### What this PR will change (summary)

- **Mojo**
  - `slot_config.mojo`: adds `anchor_mode`, `bin_width_pct`, `epsilon_scale`, `slot_limit`, etc. (integer aliases, stable).
  - `slot_engine.mojo`: adds `anchor_slot_id(focus_anchor, input_value, bin_width_pct, epsilon_scale) -> Int`.
  - `neuron.mojo`: `on_input` switches to **anchor-first** selection, reuses or clamps slot ids, and keeps your reinforcement/threshold semantics intact.


If you want me to include a follow-up PR to thread **SlotConfig** through Mojo (so `neuron.on_input` reads the real knobs instead of defaults), say the word and I’ll prep that next.
```