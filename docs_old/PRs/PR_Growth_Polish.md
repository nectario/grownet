## PR 11 — Growth polish (scalar fallback detection + “no new slot at capacity”)

### Why

1. In the **scalar** path, a neuron should mark `last_slot_used_fallback=True` any time it *wants* a brand‑new bin but can’t have one (either because the desired id is outside `[0..limit-1]` **or** you’re at capacity and the desired id doesn’t exist). This stabilizes the escalation trigger so you don’t miss growth pressure on repeated hits.
2. When a neuron is **at capacity**, we should **never create a new slot**; instead we “reuse” a deterministic existing slot (fallback). Your current code can create a new slot in some corner cases (e.g., at capacity and the chosen fallback id doesn’t exist yet), which momentarily exceeds the cap. The fix keeps the cap strict.

### Patch 1 — `src/python/slot_engine.py`

Make scalar fallback detection explicit and prevent slot creation when at capacity. Do the same “no new slot at capacity” in 2D. (Only the inner selection logic changes; public behavior is the same.)

```diff
--- a/src/python/slot_engine.py
+++ b/src/python/slot_engine.py
@@
 class SlotEngine:
     """Slot selection helpers (policy + temporal & spatial focus) with fallback markers."""
@@
-    def select_or_create_slot(self, neuron, input_value, tick_count=0):
-        """FIRST-anchor binning with capacity clamp; ensures slot exists.
-        Also sets neuron.last_slot_used_fallback True/False for growth logic.
-        """
+    def select_or_create_slot(self, neuron, input_value, tick_count=0):
+        """FIRST-anchor binning with capacity clamp.
+        Marks `neuron.last_slot_used_fallback` whenever a new bin is desired but capacity forces reuse.
+        Never allocates a brand-new slot if capacity is already reached.
+        """
         cfg = self.cfg
@@
-        sid = int(delta_pct // width)
-        # clamp to slot_limit, ensure existence
+        sid_desired = int(delta_pct // width)
+        # capacity & domain
         limit = int(getattr(cfg, "slot_limit", 16))
-        if limit > 0 and sid >= limit:
-            sid = limit - 1
         slots = neuron.slots
-        used_fallback = False
-        if sid not in slots:
-            if limit > 0 and len(slots) >= limit:
-                # reuse last id within [0, limit-1]
-                sid = min(sid, limit - 1)
-                used_fallback = True
-                if sid not in slots:
-                    slots[sid] = Weight()
-            else:
-                slots[sid] = Weight()
-        # flag for growth
+        at_capacity = (limit > 0 and len(slots) >= limit)
+
+        # Decide whether we *wanted* a new bin but must fallback.
+        want_new = (sid_desired not in slots)
+        out_of_domain = (limit > 0 and sid_desired >= limit)
+        use_fallback = out_of_domain or (at_capacity and want_new)
+
+        # Choose the actual slot id to use
+        if use_fallback and limit > 0:
+            # Prefer a deterministic existing fallback in [0..limit-1]
+            sid = (limit - 1)
+            if sid not in slots:
+                # pick any existing id (do not allocate at capacity)
+                if slots:
+                    sid = next(iter(slots.keys()))
+                else:
+                    # no slots yet; we can create the first one
+                    sid = (limit - 1)
+        else:
+            sid = sid_desired
+
+        # Ensure existence only if we are not at capacity OR the chosen sid already existed
+        if sid not in slots:
+            if at_capacity:
+                # Do not create new cells at capacity; reuse an existing one instead.
+                # (We already picked an existing sid above when at_capacity=True.)
+                # As a last resort, place a cell at sid only if this is the first ever slot.
+                if not slots:
+                    slots[sid] = Weight()
+            else:
+                slots[sid] = Weight()
+
+        # Flag for growth logic
         try:
-            neuron.last_slot_used_fallback = bool(used_fallback)
+            neuron.last_slot_used_fallback = bool(use_fallback)
         except Exception:
             pass
         return slots[sid]
@@
-    def select_or_create_slot_2d(self, neuron, row: int, col: int):
+    def select_or_create_slot_2d(self, neuron, row: int, col: int):
         """2D FIRST/ORIGIN anchor + capacity clamp; ensures spatial slot exists.
 
         Keys are (row_bin, col_bin) tuples. When capacity is saturated, reuse a
-        fallback id (limit-1, limit-1) to avoid unbounded growth. Also sets
-        neuron.last_slot_used_fallback for growth logic.
+        fallback id (limit-1, limit-1) if present; otherwise reuse any existing slot.
+        Never creates a new slot at capacity. Also sets neuron.last_slot_used_fallback.
         """
@@
-        key = (row_bin, col_bin)
-        slots = neuron.slots
-        used_fallback = False
-        if key not in slots:
-            if limit > 0 and len(slots) >= limit:
-                # reuse a deterministic fallback within domain
-                key = (limit - 1, limit - 1)
-                used_fallback = True
-                if key not in slots:
-                    slots[key] = Weight()
-            else:
-                slots[key] = Weight()
-        try:
-            neuron.last_slot_used_fallback = bool(used_fallback)
+        key_desired = (row_bin, col_bin)
+        slots = neuron.slots
+        at_capacity = (limit > 0 and len(slots) >= limit)
+        want_new = (key_desired not in slots)
+        use_fallback = (at_capacity and want_new)
+
+        if use_fallback and limit > 0:
+            key = (limit - 1, limit - 1)
+            if key not in slots:
+                # reuse any existing slot (do not create at capacity)
+                if slots:
+                    key = next(iter(slots.keys()))
+        else:
+            key = key_desired
+
+        if key not in slots:
+            if at_capacity:
+                if not slots:
+                    slots[key] = Weight()
+            else:
+                slots[key] = Weight()
+        try:
+            neuron.last_slot_used_fallback = bool(use_fallback)
         except Exception:
             pass
-        return slots[key]
+        return slots[key]
```

### Patch 2 — (optional but recommended) don’t share `SlotEngine` instances

When cloning a neuron during growth, prefer a **fresh** engine with the same config (avoid accidental shared state later).

```diff
--- a/src/python/layer.py
+++ b/src/python/layer.py
@@
-        try:
-            new_n.slot_cfg = seed_neuron.slot_cfg
-            new_n.slot_engine = seed_neuron.slot_engine
-            new_n.slot_limit = seed_neuron.slot_limit
-        except Exception:
-            pass
+        try:
+            new_n.slot_cfg   = seed_neuron.slot_cfg
+            # fresh engine with same cfg (avoid shared state)
+            from slot_engine import SlotEngine
+            new_n.slot_engine = SlotEngine(new_n.slot_cfg)
+            new_n.slot_limit  = seed_neuron.slot_limit
+        except Exception:
+            pass
```

> These two edits are tiny, safe, and keep all your existing tests/demos intact. They just make the growth trigger more faithful and keep `slot_limit` a *hard* cap.

### Test plan (fast)

- Existing `test_growth.py` should continue to pass.
- To sanity‑check the scalar path quickly:
  - Set an excitatory neuron with `slot_limit=1`, drive three novel scalars that would map to different bins; confirm the layer grows after your threshold (e.g., 1 or 2).

------

## What’s in good shape already

- **Marking** fallback usage in 2D; **cooldown** via bus `current_step`.
- **Autowiring**: outbound/inbound mesh + tract source attach; deterministic via stored rules and seeded RNG.
- **Owner** pointers set for I/O and mixed layers.
- **Docs**: `GROWTH.md` explains the escalation rule cleanly.

## Suggested tiny follow‑ups (non‑blocking)

1. **Dedup when autowiring** (belt‑and‑suspenders): if `Neuron.connect` doesn’t deduplicate internally, wrap `connect` calls with a small per‑tick `{(src_id, dst_id)}` set or check an `is_connected` helper. Prevents accidental duplicate edges if a rule is recorded twice.
2. **Cooldown unit test** (fast): Set `fallback_growth_threshold=1`, `neuron_growth_cooldown_ticks=100`, drive 2–3 fallback hits in quick succession, assert growth happens only once.
3. **Spillover layer wiring (polish)**: When `request_layer_growth` fires, consider copying *inbound* mesh rules that target the saturated layer so the new layer starts with the same upstream connections (today, you wire saturated → new only; that’s fine for a v1).

------

## Cross‑language parity plan (sketch you can hand to Codex next)

**C++**

- Add to `Neuron`:
  - `owner` backref, `lastSlotUsedFallback` (bool), `fallbackStreak`, `lastGrowthTick`.
- In `SlotEngine`:
  - Mirror the **“no new slot at capacity”** logic and **explicit fallback flag** (move inline bodies into `SlotEngine.cpp` and `#include "Neuron.h"` to avoid the incomplete‑type error you saw earlier).
- In `Layer`:
  - `tryGrowNeuron(Neuron& seed)`; set owner; clone cfg; fresh engine; append; call `region._autowireNewNeuron(...)`.
- In `Region`:
  - Track `meshRules` and `tracts`; implement `_autowireNewNeuron` similarly to Python; keep RNG seeded for determinism.
  - Optional `requestLayerGrowth(...)` with the same conservative spillover.
- In `Tract`:
  - `attachSourceNeuron(newIndex)` to register the firing hook.
- In `LateralBus`:
  - `currentStep` incremented in `decay()` to support cooldown.
- **Tests**: a small smoke (guarded) for neuron growth and autowiring; reuse your existing windowed wiring smoke harness.

**Java**

- Add the same fields to `Neuron`; compute fallback in `SlotEngine.selectOrCreateSlot(...)` and `selectOrCreateSlot2D(...)` with “no new slot at capacity”.
- `Layer.tryGrowNeuron(...)` + `Region._autowireNewNeuron(...)` + `Tract.attachSourceNeuron(...)` equivalents.
- `LateralBus.getCurrentStep()` incremented in `decay()` (you already added a decay field earlier).

**Mojo**

- Mirror the Python logic; keep it minimal for now: fields + fallback flag + `Layer.try_grow_neuron` + region mesh bookkeeping.

