# PR — Stricter Per‑Neuron Growth Guard (opt‑in, deterministic)

**Objective**
 Add two *optional* guards to the per‑neuron growth trigger, implemented identically in **Python, Java, C++, and Mojo**, without changing default behavior:

1. `fallback_growth_requires_same_missing_slot: bool = False`
    Only count a fallback toward the growth streak if the **same missing slot id** (scalar bin or 2D pair) is requested on consecutive ticks.
2. `min_delta_pct_for_growth: float = 0.0`
    Gate growth by **novelty magnitude**: only fallback requests with **delta ≥ this threshold** can contribute to the streak.
   - **2D** default: delta gate computed as `max(row_delta_pct, col_delta_pct)` (separable bins); see *ADAPT* note if you use a radial function.

**Non‑goals**

- No change to two‑phase tick, autowiring, windowed tracts, or region‑level OR trigger.
- No change to defaults: existing models behave exactly the same unless you set these knobs.

**Note:** Patch Diffs are at the bottom

------

## 1) Config additions (same semantics in all languages)

### Python — `src/python/slot_config.py`

```python
@dataclass
class SlotConfig:
    # existing fields...
    growth_enabled: bool = True
    neuron_growth_enabled: bool = True
    layer_growth_enabled: bool = False
    fallback_growth_threshold: int = 3
    neuron_growth_cooldown_ticks: int = 0
    # NEW (opt-in guards)
    fallback_growth_requires_same_missing_slot: bool = False
    min_delta_pct_for_growth: float = 0.0
```

### Java — *ADAPT: put alongside your per‑neuron growth knobs (SlotConfig or similar)*

```
src/java/ai/nektron/grownet/config/SlotConfig.java
public final class SlotConfig {
    // existing fields...
    public boolean growthEnabled = true;
    public boolean neuronGrowthEnabled = true;
    public boolean layerGrowthEnabled = false;
    public int     fallbackGrowthThreshold = 3;
    public int     neuronGrowthCooldownTicks = 0;
    // NEW (opt-in guards)
    public boolean fallbackGrowthRequiresSameMissingSlot = false;
    public double  minDeltaPctForGrowth = 0.0;
}
```

### C++ — `include/SlotConfig.h`

```cpp
struct SlotConfig {
  // existing fields...
  bool growthEnabled = true;
  bool neuronGrowthEnabled = true;
  bool layerGrowthEnabled = false;
  int  fallbackGrowthThreshold = 3;
  int  neuronGrowthCooldownTicks = 0;
  // NEW (opt-in guards)
  bool   fallbackGrowthRequiresSameMissingSlot = false;
  double minDeltaPctForGrowth = 0.0;
};
```

### Mojo — `src/mojo/slot_config.mojo`

```mojo
struct SlotConfig:
    # existing fields...
    var growth_enabled: Bool = True
    var neuron_growth_enabled: Bool = True
    var layer_growth_enabled: Bool = False
    var fallback_growth_threshold: Int = 3
    var neuron_growth_cooldown_ticks: Int = 0
    # NEW (opt-in guards)
    var fallback_growth_requires_same_missing_slot: Bool = False
    var min_delta_pct_for_growth: Float64 = 0.0
```

------

## 2) Minimal per‑neuron state (needed only when guards are used)

Add **transient** fields to the neuron core (overwritten each tick):

- `last_missing_slot_id` (**int**, -1 if none) — the desired slot id when we had to fall back.
- `fallback_streak` (**int**) — consecutive fallback count under the guard rules.
- `last_max_axis_delta_pct` (**float/double**) — for the delta gate; compute as `max(row_delta_pct, col_delta_pct)` for 2D (or scalar delta for 1D).

**Python** — `src/python/neuron.py`

```python
class Neuron:
    # existing fields...
    last_missing_slot_id: int | None = None
    fallback_streak: int = 0
    last_max_axis_delta_pct: float = 0.0
```

**Java** — `src/java/ai/nektron/grownet/core/Neuron.java`

```java
public final class Neuron {
    // existing fields...
    public int    lastMissingSlotId = -1;
    public int    fallbackStreak = 0;
    public double lastMaxAxisDeltaPct = 0.0;
}
```

**C++** — `include/Neuron.h`

```cpp
struct Neuron {
  // existing fields...
  int    lastMissingSlotId = -1;
  int    fallbackStreak = 0;
  double lastMaxAxisDeltaPct = 0.0;
};
```

**Mojo** — `src/mojo/neuron.mojo`

```mojo
struct Neuron:
    # existing fields...
    var last_missing_slot_id: Int = -1
    var fallback_streak: Int = 0
    var last_max_axis_delta_pct: Float64 = 0.0
```

> **Note:** Field names follow each language’s style; no leading underscores; descriptive identifiers only.

------

## 3) Selector updates (set desired id and delta gate each tick)

Where you compute a slot for the current input:

- Compute **desired_slot_id** (scalar bin or packed `(row_bin, col_bin)`).
- Compute **gating_delta_pct**:
  - **Scalar:** `abs(current - anchor) / max(abs(anchor), epsilon) * 100.0`
  - **2D:** `max(row_delta_pct, col_delta_pct)` (default).
     *ADAPT:* if you already compute a radial percent, you may use that instead—keep it consistent across languages.
- If slot exists → **use it** and **reset `fallback_streak`** to `0`.
- If **at capacity** and desired slot **missing** → **use fallback** and fill:
  - `last_missing_slot_id = desired_slot_id`
  - `last_max_axis_delta_pct = gating_delta_pct`
  - **do not** increment streak here; the growth engine (next section) will apply guards and update.

*(Apply the same logic in scalar and 2D selectors.)*

------

## 4) Growth trigger logic (apply both guards before incrementing streak)

Where you previously counted a fallback toward the streak, replace with:

**Python** — `src/python/growth.py` (ADAPT file/name to where you check triggers)

```python
def consider_neuron_growth(neuron: Neuron, cfg: SlotConfig, now_step: int) -> None:
    if not cfg.neuron_growth_enabled:
        neuron.fallback_streak = 0
        return

    if not neuron.last_slot_used_fallback:   # existing boolean in your code
        neuron.fallback_streak = 0
        return

    # delta gate
    if cfg.min_delta_pct_for_growth > 0.0:
        if neuron.last_max_axis_delta_pct < cfg.min_delta_pct_for_growth:
            neuron.fallback_streak = 0
            neuron.last_missing_slot_id = -1
            return

    # same-missing-slot guard
    if cfg.fallback_growth_requires_same_missing_slot:
        if neuron.prev_missing_slot_id == neuron.last_missing_slot_id:
            neuron.fallback_streak += 1
        else:
            neuron.fallback_streak = 1
            neuron.prev_missing_slot_id = neuron.last_missing_slot_id
    else:
        neuron.fallback_streak += 1

    # threshold + cooldown
    if neuron.fallback_streak >= cfg.fallback_growth_threshold and cooldown_ok(neuron, cfg, now_step):
        grow_one_neuron_like(neuron)         # existing deterministic growth
        neuron.fallback_streak = 0
        neuron.prev_missing_slot_id = -1
```

**Java/C++/Mojo** mirror this exactly in their growth paths. Keep names idiomatic:

- Java: `prevMissingSlotId`, `cooldownOk`, `growOneNeuronLike`.
- C++: `prev_missing_slot_id`, `cooldown_ok`, `grow_one_neuron_like`.
- Mojo: `prev_missing_slot_id`, `cooldown_ok`, `grow_one_neuron_like`.

> **Important:** Reset the streak whenever the fallback condition is **not** met on this tick (slot existed, or not at capacity), or when the **delta gate** fails.

------

## 5) Tests (additions)

Create or extend tests in each language:

**A) Defaults unchanged**

- With both new knobs at defaults (`False` and `0.0`), replicate an existing fallback‑streak test → growth fires exactly as before.

**B) Same‑missing‑slot guard**

- At capacity, alternate between two different missing slot ids on consecutive ticks (e.g., `(1,2)`, `(2,1)`, `(1,2)`, …).
- With `fallback_growth_requires_same_missing_slot = True`, assert that **no growth** occurs even after many ticks.

**C) Delta gate**

- Set `min_delta_pct_for_growth = 70.0`.
- Feed a sequence that repeatedly seeks a missing slot with **60%** deltas → **no growth**.
- Then feed **80%** deltas to the **same** missing slot id → growth fires after `fallback_growth_threshold`.

**D) 2D semantics**

- Use a 2D input stream; confirm that the gating delta is `max(row_delta_pct, col_delta_pct)` (or your ADAPT radial) by crafting cases where only one axis crosses the threshold → behavior matches spec.

**E) Cooldown respected**

- Ensure growth only fires when per‑neuron cooldown allows it.

------

## 6) Docs

- Add a small subsection to `docs/GROWTH.md`: **“Optional stricter neuron-growth guards”**:
  - Explain both knobs and defaults.
  - Document 2D gating delta choice (`max(axis)`, or your project’s radial if you choose that).
  - Reiterate that **capacity** AND **fallback streak** must hold; **ordinary mid‑range slots** (like 10–20%) never trigger growth on their own.

------

## 7) Commit plan (so Codex lands this cleanly)

1. **Config fields**
   - Add `fallback_growth_requires_same_missing_slot` and `min_delta_pct_for_growth` to Python/Mojo/C++/Java config types.
   - Default values: `False` and `0.0`.
2. **Neuron state**
   - Add `last_missing_slot_id`, `fallback_streak`, `last_max_axis_delta_pct` transient fields.
3. **Selector plumbing**
   - Populate `last_missing_slot_id` and `last_max_axis_delta_pct` whenever capacity forces fallback; reset streak when not in fallback.
4. **Growth trigger**
   - Apply delta gate and same‑missing‑slot guard before incrementing the streak; enforce cooldown and fire growth deterministically; reset streak and tracking.
5. **Tests**
   - Add tests A–E in each language’s test suite.
6. **Docs**
   - Update `docs/GROWTH.md`.

------

## 8) Quick usage (your requested settings)

Once merged, set:

- `fallback_growth_requires_same_missing_slot = True`
- `min_delta_pct_for_growth = 70.0`
- Keep your existing `fallback_growth_threshold` (e.g., `3`) and cooldown.

This ensures **no “10% novelty”** can escalate to a new neuron, and **only** a **repeatable, sufficiently large** novel demand at **capacity** will grow one.

------

## 9) ADAPT notes

- If your code already stores the **desired slot id** for a fallback event, reuse it instead of adding `last_missing_slot_id`.
- If your 2D selector computes a **radial percent** (rather than separable axis deltas), use that for the gate **consistently across languages**. Otherwise keep the default `max(axis)` gate.
- Keep naming idiomatic per language; avoid single/double‑character identifiers; **no leading underscores** in Python/Mojo public names.

------

Below are patch snippets to the exact file paths and method names (so you, Codex, applies with fewer ADAPT edits)

> **Notes for Codex**
>  • Filenames below match our earlier structure; if your tree differs, **ADAPT the paths** but keep the code identical.
>  • Names are descriptive; **no single/double‑character identifiers**, and **no leading underscores** in Python/Mojo.
>  • The “gating delta” for 2D is `max(row_delta_pct, col_delta_pct)` to stay consistent with separable 2D bins.

------

## PYTHON

### 1) Add the two knobs to `SlotConfig`

**File:** `src/python/slot_config.py`

```diff
@@
 @dataclass
 class SlotConfig:
@@
-    fallback_growth_threshold: int = 3
-    neuron_growth_cooldown_ticks: int = 0
+    fallback_growth_threshold: int = 3
+    neuron_growth_cooldown_ticks: int = 0
+    # --- Optional stricter guards (defaults keep behavior unchanged) ---
+    fallback_growth_requires_same_missing_slot: bool = False
+    min_delta_pct_for_growth: float = 0.0
```

### 2) Add transient per‑neuron fields

**File:** `src/python/neuron.py`

```diff
@@
 class Neuron:
@@
     # existing fields...
+    # --- Transient fields used by stricter growth guards ---
+    prev_missing_slot_id: int | None = None
+    last_missing_slot_id: int | None = None
+    fallback_streak: int = 0
+    last_max_axis_delta_pct: float = 0.0
```

### 3) Populate the fields in the 2D selector when falling back

**File:** `src/python/slot_engine.py`  *(ADAPT if your selectors live elsewhere; add the same block to scalar & 2D paths.)*

```diff
@@
 def select_or_create_slot_2d(neuron, slot_config, row_value: float, col_value: float):
     # existing anchor/percent-delta/binning logic...
@@
-    if desired_slot_id in neuron.slots:
-        neuron.last_slot_used_fallback = False
-        return desired_slot_id
+    if desired_slot_id in neuron.slots:
+        neuron.last_slot_used_fallback = False
+        neuron.fallback_streak = 0
+        neuron.prev_missing_slot_id = None
+        neuron.last_missing_slot_id = None
+        return desired_slot_id
 
     # at-capacity path → fallback
-    if len(neuron.slots) >= slot_config.slot_limit:
-        neuron.last_slot_used_fallback = True
-        return neuron.fallback_slot_id
+    if len(neuron.slots) >= slot_config.slot_limit:
+        neuron.last_slot_used_fallback = True
+        # Compute gating delta (2D): max of axis deltas (assumes you already computed row_delta_pct / col_delta_pct)
+        # If not available in local scope, recompute deterministically from row_value, col_value and anchor.
+        neuron.last_max_axis_delta_pct = max(abs(row_value - neuron.anchor_row) / max(abs(neuron.anchor_row), neuron.epsilon_scale) * 100.0,
+                                             abs(col_value - neuron.anchor_col) / max(abs(neuron.anchor_col), neuron.epsilon_scale) * 100.0)
+        neuron.last_missing_slot_id = desired_slot_id
+        return neuron.fallback_slot_id
 
     # capacity available → allocate
     neuron.last_slot_used_fallback = False
     neuron.slots[desired_slot_id] = create_new_slot(desired_slot_id)
     return desired_slot_id
```

> **Do the same in your scalar selector** (`select_or_create_slot_scalar`): set `last_max_axis_delta_pct` to the scalar percent delta, set `last_missing_slot_id` when going to fallback, and reset streak when using an existing slot.

### 4) Apply guards before incrementing the fallback streak

**File:** `src/python/growth.py`  *(ADAPT to your growth trigger locus)*

```diff
@@
-def consider_neuron_growth(neuron: Neuron, slot_config: SlotConfig, current_step: int) -> None:
+def consider_neuron_growth(neuron: Neuron, slot_config: SlotConfig, current_step: int) -> None:
     # preconditions: growth enabled, cooldown, etc. handled elsewhere or here
-    if not neuron.last_slot_used_fallback:
-        neuron.fallback_streak = 0
-        return
+    if not neuron.last_slot_used_fallback:
+        neuron.fallback_streak = 0
+        neuron.prev_missing_slot_id = None
+        neuron.last_missing_slot_id = None
+        return
 
     # --- Guard B: min delta gate ---
-    # (no-op before)
+    if slot_config.min_delta_pct_for_growth > 0.0:
+        if neuron.last_max_axis_delta_pct < slot_config.min_delta_pct_for_growth:
+            neuron.fallback_streak = 0
+            neuron.prev_missing_slot_id = None
+            return
 
     # --- Guard A: same missing slot id on consecutive ticks ---
-    neuron.fallback_streak += 1
+    if slot_config.fallback_growth_requires_same_missing_slot:
+        if neuron.prev_missing_slot_id == neuron.last_missing_slot_id:
+            neuron.fallback_streak += 1
+        else:
+            neuron.fallback_streak = 1
+            neuron.prev_missing_slot_id = neuron.last_missing_slot_id
+    else:
+        neuron.fallback_streak += 1
 
     # threshold + cooldown → grow deterministically then reset
     if (neuron.fallback_streak >= slot_config.fallback_growth_threshold
             and cooldown_ok(neuron, slot_config, current_step)):
         grow_one_neuron_like(neuron)   # existing deterministic path
-        neuron.fallback_streak = 0
+        neuron.fallback_streak = 0
+        neuron.prev_missing_slot_id = None
+        neuron.last_missing_slot_id = None
```

### 5) Tests

**File:** `src/python/tests/test_growth_guards.py` *(new)*

```python
import pytest
from src.python.slot_config import SlotConfig
from src.python.neuron import Neuron
from src.python.growth import consider_neuron_growth

def make_neuron_at_capacity(fallback_slot_id=0):
    n = Neuron()
    n.slots = {k: object() for k in range(16)}  # pretend 16 allocated
    n.fallback_slot_id = fallback_slot_id
    n.last_slot_used_fallback = True
    return n

def test_defaults_preserve_behavior():
    cfg = SlotConfig(slot_limit=16, fallback_growth_threshold=3)
    n = make_neuron_at_capacity()
    # simulate 3 consecutive fallbacks
    for _ in range(3):
        n.last_max_axis_delta_pct = 10.0
        n.last_missing_slot_id = 101
        consider_neuron_growth(n, cfg, current_step=0)
    # Expect growth once; your grow function likely mutates layer; here we assert streak reset
    assert n.fallback_streak == 0

def test_same_missing_slot_guard_blocks_alternating_pairs():
    cfg = SlotConfig(slot_limit=16, fallback_growth_threshold=3,
                     fallback_growth_requires_same_missing_slot=True)
    n = make_neuron_at_capacity()
    for i in range(6):
        n.last_max_axis_delta_pct = 90.0
        n.last_missing_slot_id = 100 if i % 2 == 0 else 200
        consider_neuron_growth(n, cfg, current_step=i)
    assert n.fallback_streak <= 1  # never reaches 3

def test_min_delta_gate_blocks_small_deltas():
    cfg = SlotConfig(slot_limit=16, fallback_growth_threshold=2,
                     min_delta_pct_for_growth=70.0)
    n = make_neuron_at_capacity()
    # 60% deltas should never count
    for _ in range(3):
        n.last_max_axis_delta_pct = 60.0
        n.last_missing_slot_id = 123
        consider_neuron_growth(n, cfg, current_step=0)
    assert n.fallback_streak == 0
    # 80% deltas should count
    for _ in range(2):
        n.last_max_axis_delta_pct = 80.0
        n.last_missing_slot_id = 123
        consider_neuron_growth(n, cfg, current_step=0)
    assert n.fallback_streak == 0  # after growth it resets
```

------

## JAVA

### 1) Add knobs to `SlotConfig`

**File:** `src/java/ai/nektron/grownet/config/SlotConfig.java`

```diff
@@
 public final class SlotConfig {
@@
-  public int  fallbackGrowthThreshold = 3;
-  public int  neuronGrowthCooldownTicks = 0;
+  public int  fallbackGrowthThreshold = 3;
+  public int  neuronGrowthCooldownTicks = 0;
+  // --- Optional stricter guards (defaults keep behavior unchanged) ---
+  public boolean fallbackGrowthRequiresSameMissingSlot = false;
+  public double  minDeltaPctForGrowth = 0.0;
}
```

### 2) Per‑neuron transient fields

**File:** `src/java/ai/nektron/grownet/core/Neuron.java`

```diff
@@
 public final class Neuron {
@@
+  // --- Transient fields used by stricter growth guards ---
+  public int    prevMissingSlotId = -1;
+  public int    lastMissingSlotId = -1;
+  public int    fallbackStreak = 0;
+  public double lastMaxAxisDeltaPct = 0.0;
}
```

### 3) Set fields when fallback is used (2D)

**File:** `src/java/ai/nektron/grownet/slot/SlotEngine.java`

```diff
@@
-  if (slots.containsKey(desiredSlotId)) {
-      neuron.lastSlotUsedFallback = false;
-      return desiredSlotId;
-  }
+  if (slots.containsKey(desiredSlotId)) {
+      neuron.lastSlotUsedFallback = false;
+      neuron.fallbackStreak = 0;
+      neuron.prevMissingSlotId = -1;
+      neuron.lastMissingSlotId = -1;
+      return desiredSlotId;
+  }
@@
-  if (slots.size() >= cfg.slotLimit) {
-      neuron.lastSlotUsedFallback = true;
-      return neuron.fallbackSlotId;
-  }
+  if (slots.size() >= cfg.slotLimit) {
+      neuron.lastSlotUsedFallback = true;
+      double rowDeltaPct = Math.abs(rowValue - neuron.anchorRow) / Math.max(Math.abs(neuron.anchorRow), neuron.epsilonScale) * 100.0;
+      double colDeltaPct = Math.abs(colValue - neuron.anchorCol) / Math.max(Math.abs(neuron.anchorCol), neuron.epsilonScale) * 100.0;
+      neuron.lastMaxAxisDeltaPct = Math.max(rowDeltaPct, colDeltaPct);
+      neuron.lastMissingSlotId = desiredSlotId;
+      return neuron.fallbackSlotId;
+  }
```

*(Apply analogous lines in the scalar selector, setting `lastMaxAxisDeltaPct` to the scalar percent.)*

### 4) Growth guard logic

**File:** `src/java/ai/nektron/grownet/growth/GrowthEngine.java`

```diff
@@
-void considerNeuronGrowth(Neuron neuron, SlotConfig cfg, long currentStep) {
-    if (!neuron.lastSlotUsedFallback) {
-        neuron.fallbackStreak = 0;
-        return;
-    }
+void considerNeuronGrowth(Neuron neuron, SlotConfig cfg, long currentStep) {
+    if (!neuron.lastSlotUsedFallback) {
+        neuron.fallbackStreak = 0;
+        neuron.prevMissingSlotId = -1;
+        neuron.lastMissingSlotId = -1;
+        return;
+    }
     // min delta gate
-    // (no-op before)
+    if (cfg.minDeltaPctForGrowth > 0.0) {
+        if (neuron.lastMaxAxisDeltaPct < cfg.minDeltaPctForGrowth) {
+            neuron.fallbackStreak = 0;
+            neuron.prevMissingSlotId = -1;
+            return;
+        }
+    }
     // same-missing-slot guard
-    neuron.fallbackStreak++;
+    if (cfg.fallbackGrowthRequiresSameMissingSlot) {
+        if (neuron.prevMissingSlotId == neuron.lastMissingSlotId) {
+            neuron.fallbackStreak++;
+        } else {
+            neuron.fallbackStreak = 1;
+            neuron.prevMissingSlotId = neuron.lastMissingSlotId;
+        }
+    } else {
+        neuron.fallbackStreak++;
+    }
     if (neuron.fallbackStreak >= cfg.fallbackGrowthThreshold && cooldownOk(neuron, cfg, currentStep)) {
         growOneNeuronLike(neuron);
-        neuron.fallbackStreak = 0;
+        neuron.fallbackStreak = 0;
+        neuron.prevMissingSlotId = -1;
+        neuron.lastMissingSlotId = -1;
     }
 }
```

### 5) Test

**File:** `src/test/java/ai/nektron/grownet/GrowthGuardsTests.java` *(new)*
 Add JUnit tests mirroring the Python cases (alternating missing ids, delta gate).

------

## C++

### 1) Add knobs to SlotConfig

**File:** `include/SlotConfig.h`

```diff
 struct SlotConfig {
@@
   int  fallbackGrowthThreshold = 3;
   int  neuronGrowthCooldownTicks = 0;
+  // --- Optional stricter guards (defaults keep behavior unchanged) ---
+  bool   fallbackGrowthRequiresSameMissingSlot = false;
+  double minDeltaPctForGrowth = 0.0;
 };
```

### 2) Per‑neuron fields

**File:** `include/Neuron.h`

```diff
 struct Neuron {
@@
+  // --- Transient fields for stricter guards ---
+  int    prev_missing_slot_id = -1;
+  int    last_missing_slot_id = -1;
+  int    fallback_streak = 0;
+  double last_max_axis_delta_pct = 0.0;
 };
```

### 3) Set fields on fallback (2D selector)

**File:** `src/SlotEngine.cpp` *(ADAPT path/name)*

```diff
@@
-  if (slots.count(desired_slot_id)) {
-      neuron.last_slot_used_fallback = false;
-      return desired_slot_id;
-  }
+  if (slots.count(desired_slot_id)) {
+      neuron.last_slot_used_fallback = false;
+      neuron.fallback_streak = 0;
+      neuron.prev_missing_slot_id = -1;
+      neuron.last_missing_slot_id = -1;
+      return desired_slot_id;
+  }
@@
-  if (slots.size() >= slot_cfg.slotLimit) {
-      neuron.last_slot_used_fallback = true;
-      return neuron.fallback_slot_id;
-  }
+  if (slots.size() >= slot_cfg.slotLimit) {
+      neuron.last_slot_used_fallback = true;
+      const double row_delta_pct = std::abs(row_value - neuron.anchor_row) / std::max(std::abs(neuron.anchor_row), neuron.epsilon_scale) * 100.0;
+      const double col_delta_pct = std::abs(col_value - neuron.anchor_col) / std::max(std::abs(neuron.anchor_col), neuron.epsilon_scale) * 100.0;
+      neuron.last_max_axis_delta_pct = std::max(row_delta_pct, col_delta_pct);
+      neuron.last_missing_slot_id = desired_slot_id;
+      return neuron.fallback_slot_id;
+  }
```

*(Add the analogous scalar branch: set `last_max_axis_delta_pct` to the scalar percent.)*

### 4) Growth guard logic

**File:** `src/GrowthEngine.cpp` *(ADAPT if logic resides elsewhere)*

```diff
@@
-void considerNeuronGrowth(Neuron& neuron, const SlotConfig& cfg, long current_step) {
-    if (!neuron.last_slot_used_fallback) {
-        neuron.fallback_streak = 0;
-        return;
-    }
+void considerNeuronGrowth(Neuron& neuron, const SlotConfig& cfg, long current_step) {
+    if (!neuron.last_slot_used_fallback) {
+        neuron.fallback_streak = 0;
+        neuron.prev_missing_slot_id = -1;
+        neuron.last_missing_slot_id = -1;
+        return;
+    }
     // delta gate
-    // (no-op before)
+    if (cfg.minDeltaPctForGrowth > 0.0) {
+        if (neuron.last_max_axis_delta_pct < cfg.minDeltaPctForGrowth) {
+            neuron.fallback_streak = 0;
+            neuron.prev_missing_slot_id = -1;
+            return;
+        }
+    }
     // same-missing-slot guard
-    neuron.fallback_streak++;
+    if (cfg.fallbackGrowthRequiresSameMissingSlot) {
+        if (neuron.prev_missing_slot_id == neuron.last_missing_slot_id) {
+            neuron.fallback_streak += 1;
+        } else {
+            neuron.fallback_streak = 1;
+            neuron.prev_missing_slot_id = neuron.last_missing_slot_id;
+        }
+    } else {
+        neuron.fallback_streak += 1;
+    }
     if (neuron.fallback_streak >= cfg.fallbackGrowthThreshold && cooldown_ok(neuron, cfg, current_step)) {
         grow_one_neuron_like(neuron);
-        neuron.fallback_streak = 0;
+        neuron.fallback_streak = 0;
+        neuron.prev_missing_slot_id = -1;
+        neuron.last_missing_slot_id = -1;
     }
 }
```

### 5) Test

**File:** `tests/growth_guards_test.cpp` *(new)*
 Add gtest cases mirroring Python (alternating missing ids blocked; 70% gate behavior).

------

## MOJO

### 1) Add knobs

**File:** `src/mojo/slot_config.mojo`

```diff
 struct SlotConfig:
@@
-    var fallback_growth_threshold: Int = 3
-    var neuron_growth_cooldown_ticks: Int = 0
+    var fallback_growth_threshold: Int = 3
+    var neuron_growth_cooldown_ticks: Int = 0
+    # --- Optional stricter guards (defaults keep behavior unchanged) ---
+    var fallback_growth_requires_same_missing_slot: Bool = False
+    var min_delta_pct_for_growth: Float64 = 0.0
```

### 2) Per‑neuron fields

**File:** `src/mojo/neuron.mojo`

```diff
 struct Neuron:
@@
+    # --- Transient fields used by stricter guards ---
+    var prev_missing_slot_id: Int = -1
+    var last_missing_slot_id: Int = -1
+    var fallback_streak: Int = 0
+    var last_max_axis_delta_pct: Float64 = 0.0
```

### 3) Set fields on fallback in 2D selector

**File:** `src/mojo/slot_engine.mojo`

```diff
@@
    if slots.contains(desired_slot_id):
        self.last_slot_used_fallback = False
+       self.fallback_streak = 0
+       self.prev_missing_slot_id = -1
+       self.last_missing_slot_id = -1
        return desired_slot_id
@@
    if slots.size >= slot_config.slot_limit:
        self.last_slot_used_fallback = True
+       let row_delta_pct = abs(row_value - self.anchor_row) / max(abs(self.anchor_row), self.epsilon_scale) * 100.0
+       let col_delta_pct = abs(col_value - self.anchor_col) / max(abs(self.anchor_col), self.epsilon_scale) * 100.0
+       self.last_max_axis_delta_pct = max(row_delta_pct, col_delta_pct)
+       self.last_missing_slot_id = desired_slot_id
        return self.fallback_slot_id
```

*(Add analogous scalar logic.)*

### 4) Growth guard logic

**File:** `src/mojo/growth_engine.mojo`

```diff
@@
 fn consider_neuron_growth(neuron: inout Neuron, cfg: SlotConfig, current_step: Int) -> None:
-    if not neuron.last_slot_used_fallback:
-        neuron.fallback_streak = 0
-        return
+    if not neuron.last_slot_used_fallback:
+        neuron.fallback_streak = 0
+        neuron.prev_missing_slot_id = -1
+        neuron.last_missing_slot_id = -1
+        return
     # delta gate
-    # (no-op before)
+    if cfg.min_delta_pct_for_growth > 0.0:
+        if neuron.last_max_axis_delta_pct < cfg.min_delta_pct_for_growth:
+            neuron.fallback_streak = 0
+            neuron.prev_missing_slot_id = -1
+            return
+        end
+    end
     # same-missing-slot guard
-    neuron.fallback_streak += 1
+    if cfg.fallback_growth_requires_same_missing_slot:
+        if neuron.prev_missing_slot_id == neuron.last_missing_slot_id:
+            neuron.fallback_streak += 1
+        else:
+            neuron.fallback_streak = 1
+            neuron.prev_missing_slot_id = neuron.last_missing_slot_id
+        end
+    else:
+        neuron.fallback_streak += 1
+    end
     if neuron.fallback_streak >= cfg.fallback_growth_threshold and cooldown_ok(neuron, cfg, current_step):
         grow_one_neuron_like(neuron)
-        neuron.fallback_streak = 0
+        neuron.fallback_streak = 0
+        neuron.prev_missing_slot_id = -1
+        neuron.last_missing_slot_id = -1
     end
```

### 5) Test

**File:** `src/mojo/tests/growth_guards_test.mojo` *(new)*
 Add tests equivalent to Python (alternation blocked by same‑missing guard; delta gate at 70%).

------

## HOW TO ENABLE YOUR PREFERRED SETTINGS

Once merged, set these in your experiment config (all languages), matching your request:

- `fallback_growth_requires_same_missing_slot = True`
- `min_delta_pct_for_growth = 70.0`

This ensures that **only** a **repeatable**, **large‑magnitude** novelty at **capacity** can trigger a new neuron—exactly your intended biological analogy.

------

## Commit plan (suggested)

1. **Config fields** (all languages)
2. **Neuron transient fields**
3. **Selector changes** (set fields on fallback; reset on normal use)
4. **Growth engine guard logic** (both guards + cooldown)
5. **Tests** (Python/Java/C++/Mojo)
6. **Docs**: small addition in `docs/GROWTH.md` under “Optional stricter neuron‑growth guards”

If you want, I can also include a tiny **smoke demo** that flips the guards on and shows no growth for mid‑range novelty (e.g., 10–20%) but growth when repeatedly exposed to ≥70% novelty.