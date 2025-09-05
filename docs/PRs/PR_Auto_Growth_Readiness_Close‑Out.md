> **Scope of this PR**
>
> - **Python**: determinize spillover wiring (`p=1.0`) and set `owner` on ND input neurons.
> - **Java**: add strict‑capacity **2D slotting** (fallback marking) and a **2D onInput** path; set `owner` on ND input neurons.
> - **Mojo**: add **“prefer last slot once”** behavior after unfreeze, and align **bus decay** with Python/Java (multiplicative inhibition, modulation reset to 1.0, step++).
>
> These are the “musts” from the checklist. Windowed tracts in Java/Mojo and “same‑kind growth” for Mojo can be a short follow‑up once this lands.

------

## PR: Auto‑Growth Readiness Close‑Out (Python + Java + Mojo)

### Python

#### 1) Deterministic spillover wiring (Region.request_layer_growth → `probability=1.0`)

> *Why*: The doc/checklist recommend `p=1.0` for spillover so growth is deterministic (easier to reason about + test).

**Patch** — `src/python/region.py`

```diff
@@
-        # connect saturated -> new with a modest probability
-        self.connect_layers(idx, new_idx, probability=0.15, feedback=False)
+        # connect saturated -> new deterministically
+        self.connect_layers(idx, new_idx, probability=1.0, feedback=False)
         return new_idx
```

#### 2) Backref on ND input neurons (owner set for completeness)

> *Why*: Inputs don’t request growth, but the checklist asks for `owner` everywhere for consistency.

**Patch** — `src/python/input_layer_nd.py`

```diff
@@
-        for i in range(total):
-            neuron = InputNeuron(f"IN[{i}]", gain=gain, epsilon_fire=epsilon_fire)
-            neuron.set_bus(self.get_bus())
-            self.get_neurons().append(neuron)
+        for index in range(total):
+            neuron = InputNeuron(f"IN[{index}]", gain=gain, epsilon_fire=epsilon_fire)
+            neuron.set_bus(self.get_bus())
+            try:
+                neuron.owner = self
+            except Exception:
+                pass
+            self.get_neurons().append(neuron)
```

------

### Java

#### 3) Strict‑capacity 2D slotting with fallback marking

> *Why*: The audit flagged missing 2D parity (no fallback marking in 2D). This mirrors Python/C++ semantics:
>
> - Per‑neuron slot limit overrides config if set
> - Never allocates a new slot at capacity (bootstrap exception on empty set)
> - Deterministic fallback key when out‑of‑domain or at capacity + new
> - Sets `lastSlotUsedFallback`

**Patch** — `JavaProject/GrowNet/src/main/java/ai/nektron/grownet/SlotEngine.java`

```diff
@@
     public class SlotEngine {
         private final SlotConfig cfg;
         public SlotEngine(SlotConfig cfg) { this.cfg = cfg; }
+        public SlotConfig getConfig() { return cfg; }
@@
         /** FIRST-anchor helper with strict capacity + fallback marking. */
         public int selectOrCreateSlot(Neuron neuron, double inputValue, SlotConfig ignored) {
             // ... (existing scalar logic unchanged)
         }
+
+        /** 2D selector with strict capacity + fallback marking.
+         *  Uses FIRST spatial anchor (row/col), bins by absolute deltas from the anchor,
+         *  packs (rowBin, colBin) into a single int key via rowBin*100000 + colBin.
+         */
+        public int selectOrCreateSlot2D(Neuron neuron, int row, int col, SlotConfig ignored) {
+            if (neuron.anchorRow < 0 || neuron.anchorCol < 0) {
+                neuron.anchorRow = row;
+                neuron.anchorCol = col;
+            }
+            final int rowBin = Math.abs(row - neuron.anchorRow);
+            final int colBin = Math.abs(col - neuron.anchorCol);
+            final int perNeuronLimit = (neuron.slotLimit >= 0 ? neuron.slotLimit : cfg.getSlotLimit());
+            final boolean atCapacity = (perNeuronLimit > 0 && neuron.getSlots().size() >= perNeuronLimit);
+            final boolean outOfDomain = (perNeuronLimit > 0 && (rowBin >= perNeuronLimit || colBin >= perNeuronLimit));
+            final int desiredKey = rowBin * 100000 + colBin;
+            final boolean wantNew = !neuron.getSlots().containsKey(desiredKey);
+            final boolean useFallback = outOfDomain || (atCapacity && wantNew);
+            final int key = (useFallback && perNeuronLimit > 0)
+                    ? (perNeuronLimit - 1) * 100000 + (perNeuronLimit - 1)
+                    : desiredKey;
+            if (!neuron.getSlots().containsKey(key)) {
+                if (atCapacity) {
+                    if (neuron.getSlots().isEmpty()) {
+                        neuron.getSlots().put(key, new Weight());
+                    }
+                } else {
+                    neuron.getSlots().put(key, new Weight());
+                }
+            }
+            neuron.lastSlotUsedFallback = useFallback;
+            return key;
+        }
     }
```

#### 4) Add a 2D on‑input path on neurons (mirrors scalar, reuses growth bookkeeping)

> *Why*: With (3) in place, this provides true 2D parity: strict cap, fallback marking, and growth escalation.

**Patch** — `JavaProject/GrowNet/src/main/java/ai/nektron/grownet/Neuron.java`

```diff
@@
     public class Neuron {
         // existing fields...
         public boolean lastSlotUsedFallback = false;
         public int     fallbackStreak = 0;
         public long    lastGrowthTick = -1L;
         public boolean preferLastSlotOnce = false;
         public Layer   owner = null;
+        // FIRST spatial anchor (2D)
+        public int anchorRow = -1;
+        public int anchorCol = -1;
@@
         public boolean onInput(double value) {
             // existing scalar path (unchanged) including growth bookkeeping
         }
+
+        /** 2D on-input path: strict capacity, fallback marking, and growth bookkeeping. */
+        public boolean onInput2D(double value, int row, int col) {
+            final int slotId = (preferLastSlotOnce && lastSlotId != null)
+                    ? lastSlotId
+                    : slotEngine.selectOrCreateSlot2D(this, row, col, /*cfg*/ null);
+            preferLastSlotOnce = false;
+            lastSlotId = slotId;
+
+            final Weight w = slots.get(slotId);
+            final double mod = bus.getModulationFactor();
+            w.reinforce(mod);
+            final boolean fired = w.updateThreshold(value);
+            setFiredLast(fired);
+            setLastInputValue(value);
+            if (fired) {
+                try { fire(value); } catch (Throwable ignored) { }
+                onOutput(value);
+            }
+            // growth bookkeeping (same as scalar)
+            try {
+                final SlotConfig C = (slotEngine == null ? null : slotEngine.getConfig());
+                if (C != null && C.isGrowthEnabled() && C.isNeuronGrowthEnabled()) {
+                    final boolean atCap = (slotLimit >= 0 && slots.size() >= slotLimit);
+                    if (atCap && lastSlotUsedFallback) fallbackStreak++; else fallbackStreak = 0;
+                    final int threshold = Math.max(1, C.getFallbackGrowthThreshold());
+                    if (owner != null && fallbackStreak >= threshold) {
+                        final long now = bus.getCurrentStep();
+                        final int cooldown = Math.max(0, C.getNeuronGrowthCooldownTicks());
+                        if (lastGrowthTick < 0 || (now - lastGrowthTick) >= cooldown) {
+                            try { owner.tryGrowNeuron(this); } catch (Throwable ignored) { }
+                            lastGrowthTick = now;
+                        }
+                        fallbackStreak = 0;
+                    }
+                }
+            } catch (Throwable ignored) { }
+            return fired;
+        }
@@
         public boolean unfreezeLastSlot() {
             if (lastSlotId == null) return false;
             Weight w = slots.getOrDefault(lastSlotId, null);
             if (w == null) return false;
             w.unfreeze();
             preferLastSlotOnce = true; // one-shot reuse after unfreeze
             return true;
         }
     }
```

#### 5) Backref on ND input neurons (owner)

**Patch** — `JavaProject/GrowNet/src/main/java/ai/nektron/grownet/InputLayerND.java`

```diff
@@
-            InputNeuron n = new InputNeuron("IN[" + i + "]", getBus(), cfg, gain, epsilonFire);
-            list.add(n);
+            InputNeuron neuron = new InputNeuron("IN[" + i + "]", getBus(), cfg, gain, epsilonFire);
+            neuron.owner = this;
+            list.add(neuron);
```

> **Note**: This PR does **not** add windowed tracts to Java. If/when you want them, I’ll add a minimal `connectLayersWindowed(...)` + tract storage and a `attachSourceNeuron(...)` re‑attach path (mirroring Python) in a follow‑up.

------

### Mojo

> **Style respected**: no identifiers starting with `_`, `fn` not `def`, every parameter typed, `struct` not `class`, and no 1–2 char variable names.

#### 6) Prefer last slot once after unfreeze

**Patch** — `src/mojo/neuron.mojo`

```diff
-struct Neuron:
+struct Neuron:
     id: String
     bus: LateralBus
     slot_cfg: SlotConfig
     slot_engine: SlotEngine
     slot_limit: Int64
     slots: Dict[Int64, Weight]
     last_slot_id: Int64 = -1
     fired_last: Bool = False
     last_input_value: Float64 = 0.0
+    prefer_last_slot_once: Bool = False
@@
 fn unfreeze_last_slot(self: inout Neuron) -> Bool:
     let target_id = self.last_slot_id
     if target_id < 0:
         return False
     if let w = self.slots.get(target_id):
         w.unfreeze()
+        self.prefer_last_slot_once = True
         return True
     return False
@@
 fn on_input(self: inout Neuron, value: Float64) -> Bool:
-    let slot_id = self.slot_engine.select_or_create_slot(self, value)
+    let slot_id = if self.prefer_last_slot_once and self.last_slot_id >= 0:
+        self.last_slot_id
+    else:
+        self.slot_engine.select_or_create_slot(self, value)
+    self.prefer_last_slot_once = False
     self.last_slot_id = slot_id
     let weight = self.slots[slot_id]
     let modulation = self.bus.get_modulation_factor()
     weight.reinforce(modulation)
     let fired = weight.update_threshold(value)
     self.fired_last = fired
     self.last_input_value = value
     if fired:
         self.fire(value)
     return fired
@@
 fn on_input_2d(self: inout Neuron, value: Float64, row: Int64, col: Int64) -> Bool:
-    let slot_id = self.slot_engine.select_or_create_slot_2d(self, row, col)
+    let slot_id = if self.prefer_last_slot_once and self.last_slot_id >= 0:
+        self.last_slot_id
+    else:
+        self.slot_engine.select_or_create_slot_2d(self, row, col)
+    self.prefer_last_slot_once = False
     self.last_slot_id = slot_id
     let weight = self.slots[slot_id]
     let modulation = self.bus.get_modulation_factor()
     weight.reinforce(modulation)
     let fired = weight.update_threshold(value)
     self.fired_last = fired
     self.last_input_value = value
     if fired:
         self.fire(value)
     return fired
```

#### 7) Align bus decay semantics (multiplicative inhibition, modulation reset to 1.0, step++)

**Patch** — `src/mojo/lateral_bus.mojo`

```diff
-struct LateralBus:
-    inhibition_factor: Float64
-    modulation_factor: Float64
-    decay_rate: Float64
+struct LateralBus:
+    inhibition_factor: Float64
+    modulation_factor: Float64
+    decay_rate: Float64
+    current_step: Int64
@@
 fn decay(self: inout LateralBus):
-    # previous behavior drifted toward 1.0
-    self.inhibition_factor = self.inhibition_factor + (1.0 - self.inhibition_factor) * self.decay_rate
-    self.modulation_factor = self.modulation_factor + (1.0 - self.modulation_factor) * self.decay_rate
+    # multiplicative inhibition, modulation reset, step++
+    self.inhibition_factor = self.inhibition_factor * self.decay_rate
+    self.modulation_factor = 1.0
+    self.current_step = self.current_step + 1
@@
 fn get_current_step(self: LateralBus) -> Int64:
     return self.current_step
```

> If your Mojo `LateralBus` already exposes `get_step()`, keep it as a trivial alias to `get_current_step()`.

------

## What this PR **does not** include (intentional)

- **Java windowed tracts** (i.e., full `connectLayersWindowed(...)` and re‑attach). Happy to submit that as **Follow‑Up A** once this lands.
- **Mojo “same kind as seed” neuron growth**. That’s **Follow‑Up B** (requires a simple kind tag on neuron structs, then selecting the right constructor in `Layer.try_grow_neuron_like`).

------

## Quick verification notes (what to expect after merge)

- **Python**
  - Region spillover layers will be wired with `p=1.0` (deterministic).
  - ND input layers now set `owner` on their input neurons.
- **Java**
  - Driving **2D inputs** into neurons will now set `lastSlotUsedFallback` correctly under tight `slotLimit`, allowing fallback streaks to trigger growth exactly like scalar.
  - ND input layers set `owner`.
- **Mojo**
  - After calling `unfreeze_last_slot()`, the next tick will reuse that slot once (parity with Python/Java).
  - Bus decay semantics are now aligned with Python/Java; cooldowns based on `current_step` behave consistently.

------

## Follow‑ups for next PR:

- **Follow‑Up A (Java)**: Minimal **windowed tracts** (`connectLayersWindowed`, tract storage, `attachSourceNeuron` re‑attachment; no reflection, no magic numbers, deterministic centers).
- **Follow‑Up B (Mojo)**: **Grow same kind as seed** (add `NeuronKind` tag, update growth logic in layer to instantiate matching struct).

------

