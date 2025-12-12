Great follow‑through—the new **Python demo** and the **C++ spatial metrics** mirror the Python behavior well and keep everything opt‑in. 👍

Below are a few **tight, low‑risk fixes** I still recommend (and a couple of tiny tests). They address edge cases I flagged earlier: (1) returning the **actual subscription count** from `connect_layers_windowed`, (2) **deduplicating** any duplicate output targets, and (3) keeping **spatial epsilon sane** at the origin so bin IDs don’t explode when using `anchor_mode="ORIGIN"`. I’ve also corrected one param name in the doc and added a quick “how to run the demo” line.

------

## Patch set (safe, scoped)

### 1) `region.py`: return unique subscription count & use sets for `sink_map`

```diff
*** a/src/python/region.py
--- b/src/python/region.py
@@
-        allowed: set[int] = set()
-        sink_map: dict[int, list[int]] = {}
-        wires = 0
+        allowed: set[int] = set()
+        sink_map: dict[int, set[int]] = {}
+        # We'll return the number of unique source subscriptions installed.
+        wires = 0
@@
-        if isinstance(dst_layer, OutputLayer2D):
+        if isinstance(dst_layer, OutputLayer2D):
             for (r0, c0) in origins:
@@
-                for rr in range(rr0, rr1):
-                    for cc2 in range(cc0, cc1):
-                        src_idx = rr * W + cc2
-                        allowed.add(src_idx)
-                        sink_map.setdefault(src_idx, []).append(center_idx)
-                        wires += 1
+                for rr in range(rr0, rr1):
+                    for cc2 in range(cc0, cc1):
+                        src_idx = rr * W + cc2
+                        allowed.add(src_idx)
+                        sink_map.setdefault(src_idx, set()).add(center_idx)
             # Create a tract that delivers directly to mapped output neurons
             from tract import Tract
-            Tract(src_layer, dst_layer, self.bus, feedback, None, allowed_source_indices=allowed, sink_map=sink_map)
+            Tract(src_layer, dst_layer, self.bus, feedback, None,
+                  allowed_source_indices=allowed, sink_map=sink_map)
+            wires = len(allowed)
         else:
@@
-                for rr in range(rr0, rr1):
-                    for cc2 in range(cc0, cc1):
-                        allowed.add(rr * W + cc2)
-                        wires += 1
+                for rr in range(rr0, rr1):
+                    for cc2 in range(cc0, cc1):
+                        allowed.add(rr * W + cc2)
             from tract import Tract
-            Tract(src_layer, dst_layer, self.bus, feedback, None, allowed_source_indices=allowed)
+            Tract(src_layer, dst_layer, self.bus, feedback, None,
+                  allowed_source_indices=allowed)
+            wires = len(allowed)
 
         return wires
```

### 2) `tract.py`: deduplicate any repeated targets in the explicit `sink_map`

```diff
*** a/src/python/tract.py
--- b/src/python/tract.py
@@
-        # If we have an explicit sink map (e.g., windowed wiring to OutputLayer2D), deliver directly
-        targets = self._sink_map.get(source_index)
+        # If we have an explicit sink map (e.g., windowed wiring to OutputLayer2D), deliver directly
+        targets = self._sink_map.get(source_index)
         if targets:
             try:
                 neurons = self.dst.get_neurons()
-                for t_idx in targets:
+                # Deduplicate in case a center was added multiple times.
+                for t_idx in (targets if isinstance(targets, set) else set(targets)):
                     if 0 <= t_idx < len(neurons):
                         n = neurons[t_idx]
                         fired = n.on_input(value)
                         if fired:
                             n.on_output(value)
                 return
```

### 3) `slot_engine.py`: sane epsilon for spatial slotting at the origin

```diff
*** a/src/python/slot_engine.py
--- b/src/python/slot_engine.py
@@
-        eps = max(1e-12, float(getattr(self.cfg, "epsilon_scale", 1e-6)))
+        # Use a sensible spatial epsilon to avoid exploding bins at ORIGIN (0,0).
+        eps = max(1.0, float(getattr(self.cfg, "epsilon_scale", 1.0)))
         denom_r = max(abs(ar), eps)
         denom_c = max(abs(ac), eps)
```

### 4) `docs/SPATIAL_FOCUS.md`: fix param name & add demo run line

```diff
*** a/docs/SPATIAL_FOCUS.md
--- b/docs/SPATIAL_FOCUS.md
@@
-edges = region.connect_layers_windowed(
-    src_idx=l_in,
+edges = region.connect_layers_windowed(
+    src_index=l_in,
     dest_index=l_hid,
@@
 Metrics prefer the furthest‑downstream `OutputLayer2D` frame; if no non‑zero output is present, they fall back to the input frame.
+
+### Quick demo
+
+```bash
+# from repo root
+PYTHONPATH=src/python python src/python/demos/spatial_focus_demo.py
+```
```

------

## Two tiny tests (append to `src/python/tests/test_spatial_focus.py`)

These validate the corrected return value and the dedup behavior for explicit sinks.

```diff
*** a/src/python/tests/test_spatial_focus.py
--- b/src/python/tests/test_spatial_focus.py
@@
 def test_spatial_metrics_centroid_and_bbox(monkeypatch):
@@
     assert r0 <= r1 and c0 <= c1
+
+
+def test_connect_layers_windowed_returns_unique_subscriptions():
+    region = Region("wires_count")
+    l_in = region.add_input_layer_2d(4, 4, 1.0, 0.01)
+    l_out = region.add_output_layer_2d(4, 4, smoothing=0.0)
+    # Single valid 4x4 window → every pixel participates exactly once.
+    wires = region.connect_layers_windowed(
+        l_in, l_out, kernel_h=4, kernel_w=4, stride_h=1, stride_w=1, padding="valid"
+    )
+    assert wires == 16
+
+
+def test_sink_map_dedup_for_output_layer():
+    from tract import Tract
+
+    class DummyNeuron:
+        def __init__(self): self.calls = 0
+        def on_input(self, v): self.calls += 1; return False
+        def on_output(self, v): pass
+
+    class DummyDst:
+        def __init__(self, n=10): self._neurons = [DummyNeuron() for _ in range(n)]
+        def get_neurons(self): return self._neurons
+
+    class DummySrc:
+        def get_neurons(self): return []
+
+    dst = DummyDst()
+    # Duplicate same center three times for a single source index
+    t = Tract(DummySrc(), dst, None, False, None,
+              allowed_source_indices=None,
+              sink_map={5: [3, 3, 3]})
+    t.on_source_fired(5, 1.0)
+    assert dst.get_neurons()[3].calls == 1
```

------

## Quick review of your new additions

- **`src/python/demos/spatial_focus_demo.py`**
   Looks good and showcases the API. Printing `m.delivered_events`, `m.active_pixels`, `m.centroid_row`, `m.centroid_col`, `m.bbox`, `m.total_slots`, `m.total_synapses` is consistent with the metrics fields.

  **Tip:** If you prefer module‑style invocation, ensure the import path supports it. Otherwise the most portable way is:

  ```bash
  PYTHONPATH=src/python python src/python/demos/spatial_focus_demo.py
  ```

- **C++ spatial metrics (`Region.h/.cpp`)**
   The mirror of Python’s logic (prefer last `OutputLayer2D`, fall back to input if the output is all‑zeros) is spot‑on. Using `std::getenv("GROWNET_ENABLE_SPATIAL_METRICS")` with a per‑region `enableSpatialMetrics` flag gives parity with Python’s env toggle + property.

  If you haven’t already, just confirm that `RegionMetrics` (not `Region`) owns:

  ```
  long long activePixels;
  double centroidRow, centroidCol;
  int bboxRowMin, bboxRowMax, bboxColMin, bboxColMax;
  ```

  since you assign through `metrics.*` in `tickImage`.

------

## What this gives you

- Deterministic, interpretable `connect_layers_windowed` return values.
- No accidental double‑delivery to the same output neuron from a single spike.
- Spatial binning that behaves well with `ORIGIN` anchoring.
- Tests that guard those behaviors going forward.

