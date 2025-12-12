Awesome—Here’s a **small, surgical PR** that implements three things:

1. `Region::setProximityConfig(const ProximityConfig&)` setter,
2. a tiny **demo** that prints `uniqueSources` for several `(kernel,stride,padding)` combos, and
3. proximity pass mirrored into `tick(...)` and `tickND(...)` (same guard as we used in `tick2D(...)`).

All code uses descriptive identifiers (no one/two‑char names) and keeps the policy optional/best‑effort. If your include paths differ, search for **ADAPT** comments.

------

# PR — Proximity Setter + Windowed Wiring Demo + Proximity in tick() and tickND()

## Summary

- Adds `Region::setProximityConfig(const ProximityConfig&)` to cleanly enable/disable proximity policy at runtime.
- Adds `src/cpp/demos/demo_windowed_parity.cpp`: prints `uniqueSources` across a few window configurations to visually sanity‑check center mapping/participation.
- Mirrors the **proximity pass** into `tick(...)` and `tickND(...)`, running **after Phase‑B** and **before endTick()/bus.decay()**, with the same **per‑step guard** used in `tick2D(...)`.

------

## Diffs

> Paths may need light adjustment if your tree differs. Keep namespace `grownet`.

### 1) `src/cpp/Region.h` — add setter declaration and (if needed) includes

```diff
*** Begin Patch
*** Update File: src/cpp/Region.h
@@
 #pragma once
 #include <vector>
 #include <memory>
+#include <optional>
+#include "ProximityConfig.h"   // ADAPT if your header lives elsewhere
+#include "ProximityEngine.h"   // ADAPT if your header lives elsewhere
 
 namespace grownet {
@@
   class Region {
   public:
@@
-    void autowireNewNeuron(Layer* sourceLayerPtr, int newNeuronIndex);
+    void autowireNewNeuron(Layer* sourceLayerPtr, int newNeuronIndex);
+
+    // Proximity policy: convenience setter (copies the config).
+    void setProximityConfig(const ProximityConfig& config);
@@
   private:
@@
-    std::vector<std::unique_ptr<TractWindowed>> windowedTracts;
+    std::vector<std::unique_ptr<TractWindowed>> windowedTracts;
 
-    // Proximity policy state
-    std::optional<ProximityConfig> proximityConfig;
-    long lastProximityTickStep = -1;
+    // Proximity policy state
+    std::optional<ProximityConfig> proximityConfig;
+    long lastProximityTickStep = -1;
   };
 
 } // namespace grownet
*** End Patch
```

> If your earlier PR already added `std::optional<ProximityConfig> proximityConfig;` and `long lastProximityTickStep`, keep them; this diff just declares the setter.

------

### 2) `src/cpp/Region.cpp` — implement setter; mirror proximity pass into `tick` and `tickND`

```diff
*** Begin Patch
*** Update File: src/cpp/Region.cpp
@@
 namespace grownet {
@@
 Tract& Region::connectLayers(int sourceIndex, int destIndex, double probability, bool feedback) {
@@
     return *tracts.back();
 }
 
+void Region::setProximityConfig(const ProximityConfig& config) {
+    proximityConfig = config;   // copy; disable by clearing has_value() if needed
+}
+
 int Region::connectLayersWindowed(int sourceIndex, int destIndex,
                                   int kernelH, int kernelW,
                                   int strideH, int strideW,
                                   const std::string& padding,
                                   bool feedback) {
@@
 RegionMetrics Region::tick(const std::string& port, double value) {
     RegionMetrics metrics;
@@
-    layers[edgeIndex]->forward(value);
+    layers[edgeIndex]->forward(value);   // Phase A (+ Phase B inside layer graph)
     metrics.incDeliveredEvents(1);
 
+    // Proximity pass (policy-layer), after Phase-B and before endTick/decay
+    try {
+        if (proximityConfig.has_value() && proximityConfig->proximityConnectEnabled) {
+            const long currentStep = bus.getCurrentStep();
+            if (currentStep != lastProximityTickStep) {
+                ProximityEngine::Apply(*this, *proximityConfig);
+                lastProximityTickStep = currentStep;
+            }
+        }
+    } catch (...) { /* best-effort only */ }
+
     for (auto& layer : layers) layer->endTick();
     bus.decay();
@@
     return metrics;
 }
@@
 RegionMetrics Region::tickND(const std::string& port, const std::vector<double>& flat, const std::vector<int>& shape) {
     RegionMetrics metrics;
@@
-    inputNd->forwardND(flat, shape);
+    inputNd->forwardND(flat, shape);     // Phase A (+ Phase B inside layer graph)
     metrics.incDeliveredEvents(1);
 
+    // Proximity pass (policy-layer), after Phase-B and before endTick/decay
+    try {
+        if (proximityConfig.has_value() && proximityConfig->proximityConnectEnabled) {
+            const long currentStep = bus.getCurrentStep();
+            if (currentStep != lastProximityTickStep) {
+                ProximityEngine::Apply(*this, *proximityConfig);
+                lastProximityTickStep = currentStep;
+            }
+        }
+    } catch (...) { /* best-effort only */ }
+
     for (auto& layer : layers) layer->endTick();
     bus.decay();
@@
     return metrics;
 }
 
 } // namespace grownet
*** End Patch
```

> We left your `tick2D(...)` proximity integration as‑is from the previous PR. Now all three tick paths are consistent.

------

### 3) New demo: `src/cpp/demos/demo_windowed_parity.cpp`

```diff
*** Begin Patch
*** Add File: src/cpp/demos/demo_windowed_parity.cpp
+#include <iostream>
+#include <tuple>
+#include <string>
+#include <vector>
+#include "Region.h"           // ADAPT include path if needed
+
+// Simple executable that prints uniqueSources for a few window configs.
+// Build target: demo_windowed_parity
+
+using grownet::Region;
+
+struct WindowConfig {
+    int kernelH;
+    int kernelW;
+    int strideH;
+    int strideW;
+    std::string padding;
+};
+
+static int run_once_and_report(const WindowConfig& cfg) {
+    Region demoRegion("windowed_demo");
+    const int src = demoRegion.addInputLayer2D(16, 16, /*gain*/1.0, /*epsilonFire*/0.0);
+    const int dst = demoRegion.addOutputLayer2D(16, 16, /*smoothing*/0.0);
+    const int uniqueSources = demoRegion.connectLayersWindowed(
+        src, dst,
+        cfg.kernelH, cfg.kernelW,
+        cfg.strideH, cfg.strideW,
+        cfg.padding, /*feedback=*/false);
+    std::cout << "kernel=(" << cfg.kernelH << "x" << cfg.kernelW
+              << "), stride=(" << cfg.strideH << "x" << cfg.strideW
+              << "), padding=" << cfg.padding
+              << "  -> uniqueSources=" << uniqueSources << std::endl;
+    return uniqueSources;
+}
+
+int main() {
+    std::vector<WindowConfig> configs = {
+        {3, 3, 1, 1, "same"},
+        {5, 5, 1, 1, "same"},
+        {7, 7, 2, 2, "same"},
+        {3, 3, 2, 2, "valid"}
+    };
+    for (const auto& cfg : configs) {
+        (void)run_once_and_report(cfg);
+    }
+    return 0;
+}
+
*** End Patch
```

------

### 4) `CMakeLists.txt` — add demo target (and keep tests unchanged)

```diff
*** Begin Patch
*** Update File: CMakeLists.txt
@@
 # Core sources already added elsewhere …
 
+# ---- Demo: windowed parity ----
+add_executable(demo_windowed_parity
+  src/cpp/demos/demo_windowed_parity.cpp
+)
+target_link_libraries(demo_windowed_parity PRIVATE grownet_core)
+
*** End Patch
```

> If you keep demos under a different path/target name, adjust accordingly.

------

## Build & Run

```bash
# Build
cmake -S . -B build
cmake --build build -j

# Run the demo
./build/demo_windowed_parity
# Example output:
# kernel=(3x3), stride=(1x1), padding=same  -> uniqueSources=256
# kernel=(5x5), stride=(1x1), padding=same  -> uniqueSources=256
# kernel=(7x7), stride=(2x2), padding=same  -> uniqueSources=256
# kernel=(3x3), stride=(2x2), padding=valid -> uniqueSources=196
```

*(The exact last number depends on geometry; the demo is for quick eyeballing, not a formal test.)*

------

## Notes & Guardrails

- The proximity pass remains **optional** and deterministic; if `proximityConfig` is not set or disabled, nothing runs.
- We placed the proximity call at the same spot for **all** ticks: **after Phase‑B** but **before** `endTick()` and `bus.decay()`. That preserves cooldown semantics tied to `bus.current_step`.
- Style is respected: descriptive names; no single/double‑character identifiers in new code.

If you’d like, I can also add a tiny CLI flag to the demo to vary `height/width` or print a couple of sampled `(source→center)` index pairs for extra clarity.