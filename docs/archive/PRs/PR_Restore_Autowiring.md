------

## Two quick notes from your diff

1. **Mojo autowiring likely got dropped.**
    In your previous code, `end_tick` called `region.autowire_new_neuron_by_ref(self, new_unified_index)` after a neuron was grown. In the diff you posted, those lines were removed, and the new `try_grow_neuron(...)` you showed returns an index but (in the snippet you pasted) doesn’t call the region to autowire. If the helper doesn’t invoke autowiring internally, please re‑add it (either inside the helper or immediately after the call). Without it, a grown neuron won’t be connected, and growth will appear to “do nothing”.
2. **Naming guideline in Mojo:**
    You asked for **no single‑ or double‑character variable names** in Mojo. In your `try_grow_neuron` you still have `C` and `j`. The patch below renames them to descriptive names (e.g., `slot_config`, `group_index`). I’ve kept everything else identical.

------

## Minimal PR (Mojo): restore autowiring + fix variable names

> **Files touched:** `src/mojo/layer.mojo`
>  **What this does:**
>
> - Calls `region.autowire_new_neuron_by_ref` right after we grow, so wiring is not lost.
> - Renames short variable names (`C`, `j`) to descriptive ones to meet your style guide.

### Patch to paste

```diff
*** a/src/mojo/layer.mojo
--- b/src/mojo/layer.mojo
@@
-    # Same-kind neuron growth helper (E/I/M), returns unified neuron index
-    fn try_grow_neuron(mut self, seed: Neuron) -> Int:
-        var C = seed.slot_cfg
-        # Determine seed kind by membership
-        var j = 0
-        while j < self.neurons_inh.len:
-            if self.neurons_inh[j].core == seed:
-                var neu_i = InhibitoryNeuron("G" + String(self.get_neurons().len))
-                neu_i.core.bus = self.bus
-                neu_i.core.slot_cfg = C
-                neu_i.core.slot_engine = SlotEngine(C)
-                neu_i.core.slot_limit = seed.slot_limit
-                self.neurons_inh.append(neu_i)
-                return (self.neurons_inh.len - 1)  # unified = inh index
-            j = j + 1
-        j = 0
-        while j < self.neurons_mod.len:
-            if self.neurons_mod[j].core == seed:
-                var neu_m = ModulatoryNeuron("G" + String(self.get_neurons().len))
-                neu_m.core.bus = self.bus
-                neu_m.core.slot_cfg = C
-                neu_m.core.slot_engine = SlotEngine(C)
-                neu_m.core.slot_limit = seed.slot_limit
-                self.neurons_mod.append(neu_m)
-                return self.neurons_inh.len + (self.neurons_mod.len - 1)
-            j = j + 1
-        # Default to excitatory
-        var neu_e = ExcitatoryNeuron("G" + String(self.get_neurons().len))
-        neu_e.core.bus = self.bus
-        neu_e.core.slot_cfg = C
-        neu_e.core.slot_engine = SlotEngine(C)
-        neu_e.core.slot_limit = seed.slot_limit
-        self.neurons_exc.append(neu_e)
-        return self.neurons_inh.len + self.neurons_mod.len + (self.neurons_exc.len - 1)
+    # Same-kind neuron growth helper (E/I/M), returns unified neuron index and autowires it
+    fn try_grow_neuron(mut self, seed: Neuron) -> Int:
+        var slot_config = seed.slot_cfg
+        # Determine seed kind by membership
+        var group_index = 0
+        while group_index < self.neurons_inh.len:
+            if self.neurons_inh[group_index].core == seed:
+                var new_inhibitory = InhibitoryNeuron("G" + String(self.get_neurons().len))
+                new_inhibitory.core.bus = self.bus
+                new_inhibitory.core.slot_cfg = slot_config
+                new_inhibitory.core.slot_engine = SlotEngine(slot_config)
+                new_inhibitory.core.slot_limit = seed.slot_limit
+                self.neurons_inh.append(new_inhibitory)
+                var new_unified_index = (self.neurons_inh.len - 1)  # unified = inhibitory index
+                if (self.region is not None) and (self.region.autowire_new_neuron_by_ref is not None):
+                    self.region.autowire_new_neuron_by_ref(self, new_unified_index)
+                return new_unified_index
+            group_index = group_index + 1
+
+        group_index = 0
+        while group_index < self.neurons_mod.len:
+            if self.neurons_mod[group_index].core == seed:
+                var new_modulatory = ModulatoryNeuron("G" + String(self.get_neurons().len))
+                new_modulatory.core.bus = self.bus
+                new_modulatory.core.slot_cfg = slot_config
+                new_modulatory.core.slot_engine = SlotEngine(slot_config)
+                new_modulatory.core.slot_limit = seed.slot_limit
+                self.neurons_mod.append(new_modulatory)
+                var new_unified_index_mod = self.neurons_inh.len + (self.neurons_mod.len - 1)
+                if (self.region is not None) and (self.region.autowire_new_neuron_by_ref is not None):
+                    self.region.autowire_new_neuron_by_ref(self, new_unified_index_mod)
+                return new_unified_index_mod
+            group_index = group_index + 1
+
+        # Default to excitatory
+        var new_excitatory = ExcitatoryNeuron("G" + String(self.get_neurons().len))
+        new_excitatory.core.bus = self.bus
+        new_excitatory.core.slot_cfg = slot_config
+        new_excitatory.core.slot_engine = SlotEngine(slot_config)
+        new_excitatory.core.slot_limit = seed.slot_limit
+        self.neurons_exc.append(new_excitatory)
+        var new_unified_index_exc = self.neurons_inh.len + self.neurons_mod.len + (self.neurons_exc.len - 1)
+        if (self.region is not None) and (self.region.autowire_new_neuron_by_ref is not None):
+            self.region.autowire_new_neuron_by_ref(self, new_unified_index_exc)
+        return new_unified_index_exc
@@
-                            # Grow same kind via helper
-                            var new_unified_index = self.try_grow_neuron(n)
+                            # Grow same kind via helper (includes autowiring)
+                            var new_unified_index = self.try_grow_neuron(n)
                             n.last_growth_tick = now
                             n.fallback_streak = 0
```

> If you already autowire in a different place, keep either the helper’s autowire block **or** the call-site autowire—**not both**—to avoid duplicate edges.

------

## Optional (Mojo) naming clean‑up you may want next

You also have earlier Mojo code (e.g., `region.mojo::connect_layers_windowed`) using short names like `H`, `W`, `KH`, `KW`, `SH`, `SW`. If you want that to follow your guideline too, I can provide a follow‑up patch to rename those to `source_height`, `source_width`, `kernel_height`, `kernel_width`, `stride_height`, `stride_width`, and `same_padding`. Functionality remains unchanged; it just improves clarity and keeps the codebase consistent.

------

## Tiny smoke checks (quick to run locally)

- **Mojo growth + autowire smoke**
  1. Drive inputs until a neuron grows (use a small `slot_limit` and low `fallback_growth_threshold`).
  2. On the tick growth occurs, verify:
     - neuron count increased in the layer
     - the new neuron has at least one inbound or outbound synapse (autowiring ran)
     - subsequent ticks propagate activity through that neuron without errors
- **Java 2D path quick check**
  - With `selectOrCreateSlot2D` and `onInput2D` now present, confirm a simple 2D input series:
    - respects strict slot capacity (no brand‑new slots once the limit is reached, except the bootstrap case)
    - sets `lastSlotUsedFallback` when a new bin is desired but capacity forces reuse



