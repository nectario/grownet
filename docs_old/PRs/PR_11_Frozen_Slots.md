## PR 11: Frozen Slots — per‑slot stability (opt‑in, no behavior change by default)

### Summary

- Introduce `frozen` on each `Weight` (slot).
- When a slot is **frozen**:
  - **Skip reinforcement** and **skip θ updates** (including first‑imprint).
  - **Still evaluates** firing against its current `theta`/`strength` (so it can continue to participate).
- Add convenience helpers on `Neuron` to **freeze/unfreeze the last slot** it selected.
- Works for **scalar** and **2D** slotting (Python & Mojo); Java/C++ cover scalar by default.

------

## Patches

> Paths are relative to repo root. Codex can apply fuzzy context; exact line numbers not required.

### Python

#### 1) `src/python/weight.py`

```diff
--- a/src/python/weight.py
+++ b/src/python/weight.py
@@
 class Weight:
     def __init__(self):
         self.strength = 0.0
         self.theta = 0.0
         self.seen_first = False
+        # --- Frozen-slot support (opt-in) ---
+        self.frozen = False
+
+    # Frozen controls
+    def freeze(self) -> None:
+        self.frozen = True
+
+    def unfreeze(self) -> None:
+        self.frozen = False
+
+    def is_frozen(self) -> bool:
+        return bool(self.frozen)
@@
-    def reinforce(self, modulation_factor):
-        """Increase strength with a small step scaled by modulation."""
+    def reinforce(self, modulation_factor):
+        """Increase strength with a small step scaled by modulation.
+        Frozen slots ignore reinforcement entirely."""
+        if self.frozen:
+            return self.strength
         step = 0.02 * float(modulation_factor)
         self.strength = self.strength + step
         return self.strength
@@
-    def update_threshold(self, input_value, beta=0.05, eta=0.01, r_star=0.1, eps=1e-3):
-        """T0 imprint + T2 homeostasis; return whether threshold is crossed."""
+    def update_threshold(self, input_value, beta=0.05, eta=0.01, r_star=0.1, eps=1e-3):
+        """T0 imprint + T2 homeostasis; return whether threshold is crossed.
+        Frozen slots do not update theta/first-seen/EMA; they only evaluate firing."""
+        if self.frozen:
+            v = float(input_value)
+            return (abs(v) > self.theta) or (self.strength > self.theta)
         value_float = float(input_value)
         # First observation "imprint"
         if not self.seen_first:
             self.theta = abs(value_float) * (1.0 + eps)
             self.seen_first = True
```

#### 2) `src/python/neuron.py`

```diff
--- a/src/python/neuron.py
+++ b/src/python/neuron.py
@@
     def __init__(self, neuron_id, bus=None, slot_cfg=None, slot_limit=-1):
@@
-        self.fire_hooks = []  # callbacks: fn(neuron, value)
+        self.fire_hooks = []  # callbacks: fn(neuron, value)
+        # Remember last selected slot (scalar or 2D) for convenience freezing.
+        self._last_slot = None
@@
     def on_input(self, value):
         """Select/reinforce a slot, update threshold, and optionally fire."""
-        slot = self.slot_engine.select_or_create_slot(self, value)
+        slot = self.slot_engine.select_or_create_slot(self, value)
+        self._last_slot = slot
         mod = 1.0
         if self.bus is not None:
             mod = self.bus.get_modulation_factor()
         slot.reinforce(modulation_factor=mod)
         fired = slot.update_threshold(value)
@@
     def on_input_2d(self, value: float, row: int, col: int) -> bool:
@@
-        slot = self.slot_engine.select_or_create_slot_2d(self, int(row), int(col))
+        slot = self.slot_engine.select_or_create_slot_2d(self, int(row), int(col))
+        self._last_slot = slot
         # reinforcement scaled by modulation
         mod = 1.0
         if self.bus is not None:
             mod = self.bus.get_modulation_factor()
         slot.reinforce(modulation_factor=mod)
@@
+    # ---------- frozen-slot convenience ----------
+    def freeze_last_slot(self) -> bool:
+        """Freeze the most recently selected slot (if any)."""
+        s = getattr(self, "_last_slot", None)
+        if s is None:
+            return False
+        try:
+            s.freeze()
+            return True
+        except Exception:
+            return False
+
+    def unfreeze_last_slot(self) -> bool:
+        s = getattr(self, "_last_slot", None)
+        if s is None:
+            return False
+        try:
+            s.unfreeze()
+            return True
+        except Exception:
+            return False
```

------

### Java

#### 1) `JavaProject/GrowNet/src/main/java/ai/nektron/grownet/Weight.java`

```diff
--- a/JavaProject/GrowNet/src/main/java/ai/nektron/grownet/Weight.java
+++ b/JavaProject/GrowNet/src/main/java/ai/nektron/grownet/Weight.java
@@
 public final class Weight {
     private double strength;
     private double theta;
     private boolean firstSeen;
+    // --- Frozen-slot support (opt-in) ---
+    private boolean frozen = false;
+
+    public void freeze()   { this.frozen = true; }
+    public void unfreeze() { this.frozen = false; }
+    public boolean isFrozen() { return frozen; }
@@
-    public double reinforce(double modulationFactor) {
+    public double reinforce(double modulationFactor) {
+        if (frozen) return strength;
         strength += 0.02 * modulationFactor;
         return strength;
     }
@@
-    public boolean updateThreshold(double inputValue) {
+    public boolean updateThreshold(double inputValue) {
+        if (frozen) {
+            double v = inputValue;
+            return (Math.abs(v) > theta) || (strength > theta);
+        }
         // First observation "imprint"
         if (!firstSeen) {
             theta = Math.abs(inputValue) * (1.0 + 1e-3);
             firstSeen = true;
         }
         boolean fired = (Math.abs(inputValue) > theta) || (strength > theta);
         // ... existing adaptation / EMA code remains ...
         return fired;
     }
 }
```

#### 2) `JavaProject/GrowNet/src/main/java/ai/nektron/grownet/Neuron.java`

```diff
--- a/JavaProject/GrowNet/src/main/java/ai/nektron/grownet/Neuron.java
+++ b/JavaProject/GrowNet/src/main/java/ai/nektron/grownet/Neuron.java
@@
-    private final Map<Integer, Weight> slots = new HashMap<>();
+    private final Map<Integer, Weight> slots = new HashMap<>();
+    private Integer lastSlotId = null; // remember most recent slot id
@@
     public boolean onInput(double value) {
-        final int slotId = slotEngine.selectOrCreateSlot(this, value, /*cfg*/ null);
+        final int slotId = slotEngine.selectOrCreateSlot(this, value, /*cfg*/ null);
+        lastSlotId = slotId;
         Weight slot = slots.get(slotId); // existence ensured by SlotEngine
         double mod = (bus != null) ? bus.getModulationFactor() : 1.0;
         slot.reinforce(mod);
         boolean fired = slot.updateThreshold(value);
         if (fired) onOutput(value);
         return fired;
     }
+
+    // -------- Frozen-slot convenience --------
+    public boolean freezeLastSlot() {
+        if (lastSlotId == null) return false;
+        Weight w = slots.get(lastSlotId);
+        if (w == null) return false;
+        w.freeze(); return true;
+    }
+    public boolean unfreezeLastSlot() {
+        if (lastSlotId == null) return false;
+        Weight w = slots.get(lastSlotId);
+        if (w == null) return false;
+        w.unfreeze(); return true;
+    }
```

> No other Java code needs to change; existing demos/tests continue to run. Frozen slots are opt‑in.

------

### C++

#### 1) `src/cpp/Weight.h`

```diff
--- a/src/cpp/Weight.h
+++ b/src/cpp/Weight.h
@@
 class Weight {
 public:
     Weight() = default;
@@
 private:
     double strengthValue {0.0};
     double thresholdValue {0.0};
     bool   firstSeen {false};
+    // --- Frozen-slot support (opt-in) ---
+    bool   frozen {false};
 public:
+    inline void freeze()   { frozen = true; }
+    inline void unfreeze() { frozen = false; }
+    inline bool isFrozen() const { return frozen; }
@@
-    inline double reinforce(double modulationFactor) {
-        strengthValue += (0.02 * modulationFactor);
-        return strengthValue;
-    }
+    inline double reinforce(double modulationFactor) {
+        if (frozen) return strengthValue;
+        strengthValue += (0.02 * modulationFactor);
+        return strengthValue;
+    }
@@
-    bool updateThreshold(double inputValue) {
+    bool updateThreshold(double inputValue) {
+        if (frozen) {
+            const double v = inputValue;
+            return (std::abs(v) > thresholdValue) || (strengthValue > thresholdValue);
+        }
         // T0 imprint + drift…
         if (!firstSeen) {
             thresholdValue = std::abs(inputValue) * (1.0 + 1e-3);
             firstSeen = true;
         }
         const bool fired = (std::abs(inputValue) > thresholdValue) || (strengthValue > thresholdValue);
         // …existing adaptation…
         return fired;
     }
 };
```

#### 2) `src/cpp/Neuron.h`  (tiny helpers; no ABI break)

```diff
--- a/src/cpp/Neuron.h
+++ b/src/cpp/Neuron.h
@@
     std::unordered_map<int, Weight>& getSlots() { return slots; }
@@
+    // Remember last slot id for convenience freezing.
+    int lastSlotId {-1};
+    inline void setLastSlotId(int id) { lastSlotId = id; }
+    inline int  getLastSlotId() const { return lastSlotId; }
+    inline bool freezeLastSlot() {
+        auto it = slots.find(lastSlotId);
+        if (it == slots.end()) return false;
+        it->second.freeze(); return true;
+    }
+    inline bool unfreezeLastSlot() {
+        auto it = slots.find(lastSlotId);
+        if (it == slots.end()) return false;
+        it->second.unfreeze(); return true;
+    }
```

#### 3) `src/cpp/SlotEngine.h` & `src/cpp/SlotEngine.cpp`

(ensure we **record** the last slot id when selecting)

```diff
--- a/src/cpp/SlotEngine.h
+++ b/src/cpp/SlotEngine.h
@@
     Weight& selectOrCreateSlot(Neuron& neuron, double inputValue) const;
--- a/src/cpp/SlotEngine.cpp
+++ b/src/cpp/SlotEngine.cpp
@@
 Weight& SlotEngine::selectOrCreateSlot(Neuron& neuron, double inputValue) const {
     // ... existing logic to compute slotId ...
     const int slotId = /* existing binning/selection result */;
     auto& slots = neuron.getSlots();
     auto it = slots.find(slotId);
     if (it == slots.end()) it = slots.emplace(slotId, Weight{}).first;
+    // Record "last used" for convenience freezing.
+    neuron.setLastSlotId(slotId);
     return it->second;
 }
```

> If `selectOrCreateSlot` is inline‑only in the header in your tree, add the `neuron.setLastSlotId(slotId);` there instead.

------

### Mojo

#### 1) `src/mojo/weight.mojo`  *(new or patched if present)*

```diff
--- a/src/mojo/weight.mojo
+++ b/src/mojo/weight.mojo
+struct Weight:
+    var strength: Float64 = 0.0
+    var theta:    Float64 = 0.0
+    var seen_first: Bool = False
+    # --- Frozen-slot support (opt-in) ---
+    var frozen: Bool = False
+
+    fn freeze(mut self) -> None:    self.frozen = True
+    fn unfreeze(mut self) -> None:  self.frozen = False
+    fn is_frozen(self) -> Bool:     return self.frozen
+
+    fn reinforce(mut self, modulation_factor: Float64) -> Float64:
+        if self.frozen: return self.strength
+        self.strength = self.strength + 0.02 * modulation_factor
+        return self.strength
+
+    fn update_threshold(mut self, input_value: Float64,
+                        beta: Float64 = 0.05, eta: Float64 = 0.01,
+                        r_star: Float64 = 0.1, eps: Float64 = 1e-3) -> Bool:
+        if self.frozen:
+            let v = input_value
+            return (abs(v) > self.theta) or (self.strength > self.theta)
+        if not self.seen_first:
+            self.theta = abs(input_value) * (1.0 + eps)
+            self.seen_first = True
+        # … keep your existing adaptation here …
+        return (abs(input_value) > self.theta) or (self.strength > self.theta)
```

#### 2) `src/mojo/neuron.mojo`

```diff
--- a/src/mojo/neuron.mojo
+++ b/src/mojo/neuron.mojo
@@
     var last_fired: Bool = False
+    var last_slot_id: Int = -1  # remember last selected slot id
@@
     fn on_input(mut self, value: Float64, modulation_factor: Float64) -> Bool:
         # ... choose/create slot id via SlotEngine ...
         let slot_id = self.slot_engine.select_anchor_slot_id(self.last_input_value, value,
                                                              self.cfg.bin_width_pct, self.cfg.epsilon_scale)
         self.last_slot_id = slot_id
         let slot = self.get_or_create_slot(slot_id)
         slot.reinforce(modulation_factor)
         let fired = slot.update_threshold(value)
         if fired: self.fire(value)
         return fired
+
+    fn freeze_last_slot(mut self) -> Bool:
+        if self.last_slot_id < 0: return False
+        let slot = self.get_or_create_slot(self.last_slot_id)
+        slot.freeze(); return True
+
+    fn unfreeze_last_slot(mut self) -> Bool:
+        if self.last_slot_id < 0: return False
+        let slot = self.get_or_create_slot(self.last_slot_id)
+        slot.unfreeze(); return True
```

> If your neuron keeps slots in a dictionary, `get_or_create_slot` is whatever helper you already have (or inline a small lookup+insert).

------

## Usage examples

> These are tiny **opt‑in** snippets; they don’t change defaults.

### Python

```python
from region import Region

r = Region("freeze-demo")
l_in = r.add_input_layer_2d(4, 4, 1.0, 0.01)
l_h  = r.add_layer(excitatory_count=8, inhibitory_count=0, modulatory_count=0)
r.connect_layers(l_in, l_h, probability=1.0, feedback=False)
r.bind_input("pixels", [l_in])

# Drive once to create/select a slot
r.tick("pixels", 0.7)  # or tick_2d(...)

n = r.get_layers()[l_h].get_neurons()[0]
n.freeze_last_slot()      # <— future reinforcement/θ-updates for this slot are disabled
r.tick("pixels", 0.9)     # slot still participates in firing but won’t adapt

n.unfreeze_last_slot()    # re-enable adaptation
```

### Java

```java
Region region = new Region("freeze-demo");
int in = region.addInputLayer2D(4, 4, 1.0, 0.01);
int hid = region.addLayer(8, 0, 0);
region.connectLayers(in, hid, 1.0, false);
region.bindInput("pixels", List.of(in));

region.tick("pixels", 0.7); // establish a slot
Neuron n = region.getLayers().get(hid).getNeurons().get(0);
n.freezeLastSlot();

region.tick("pixels", 0.9); // slot fires but is stable (no reinforcement/θ changes)
n.unfreezeLastSlot();
```

### C++

```cpp
using namespace grownet;
Region region("freeze-demo");
int in  = region.addInputLayer2D(4,4,1.0,0.01);
int hid = region.addLayer(8,0,0);
region.connectLayers(in, hid, 1.0, false);
region.bindInput("pixels", {in});

region.tick("pixels", 0.7); // select a slot
auto& neuron = *region.getLayers()[hid]->getNeurons()[0];
neuron.freezeLastSlot();

region.tick("pixels", 0.9); // frozen slot still evaluates firing but doesn’t adapt
neuron.unfreezeLastSlot();
```

### Mojo

```mojo
var region = Region("freeze-demo")
let in  = region.add_input_layer_2d(4, 4, 1.0, 0.01)
let hid = region.add_layer(8, 0, 0)
region.connect_layers(in, hid, probability=1.0, feedback=False)
region.bind_input("pixels", [in])

_ = region.tick("pixels", 0.7)    # establish a slot
let n = region.get_layers()[hid].get_neurons()[0]
n.freeze_last_slot()

_ = region.tick("pixels", 0.9)    # frozen slot stays fixed
n.unfreeze_last_slot()
```

------

## Notes & compatibility

- **Backwards‑compatible:** Default behavior is unchanged; no existing code needs modifications.
- **Where the flag lives:** The `frozen` flag is stored on **Weight (slot)**, not on the neuron, so different slots on the same neuron can be frozen independently.
- **When to freeze:** Freeze **after** a slot has meaningfully adapted (post‑imprint), so it retains useful `theta/strength`.
- **2D slotting:** Python/Mojo automatically track the last spatial slot too (`_last_slot` / `last_slot_id`), so you can freeze a location‑specific compartment the same way.