## PR 10 - Spatial focus polish: docs clarifications

**Spatial focus polish: docs clarifications + C++ windowed wiring (deterministic Input2D→Output2D) + return semantics**

## Summary

- **Docs**
  - Add “Even kernels & center rule” for `"same"` padding.
  - Clarify that `connect_layers_windowed` (Python) and `connectLayersWindowed` (C++) **return the number of unique source subscriptions** (not raw connection count).
- **C++**
  - Implement `Region::connectLayersWindowed(...)`:
    - When **dest is `OutputLayer2D`**: for each sliding window, connect all source pixels in the window to the **center** output neuron (floor index). Deduplicates pairs in a local set to avoid duplicate edges.
    - When **dest is not `OutputLayer2D`**: deterministically connect each **participating source pixel** to **all** destination neurons (documented stopgap until 2D‑context propagation is added).
    - Return **`allowed.size()`**, where `allowed` is the set of unique source indices that appear in any window.
  - Keep default behavior unchanged elsewhere.

## Patches

> **Note:** Paths assume repo root. Codex can apply fuzzy context; exact line numbers are not required.

### 1) docs/SPATIAL_FOCUS.md — clarify center rule & return semantics

```diff
--- a/docs/SPATIAL_FOCUS.md
+++ b/docs/SPATIAL_FOCUS.md
@@
 ## Windowed wiring helper
@@
 Use `Region.connect_layers_windowed(...)` to wire an `InputLayer2D` to a destination layer deterministically using sliding windows:
@@
-edges = region.connect_layers_windowed(
-    src_index=l_in,
-    dest_index=l_hid,
-    kernel_h=2, kernel_w=2,
-    stride_h=2, stride_w=2,
-    padding="valid",
-)
+edges = region.connect_layers_windowed(
+    src_index=l_in,
+    dest_index=l_hid,
+    kernel_h=2, kernel_w=2,
+    stride_h=2, stride_w=2,
+    padding="valid",
+)
@@
-- Returns a deterministic count of “wires” (subscription hooks) created.
+- **Return value semantics:** returns the number of **unique source subscriptions** (i.e., distinct source pixels that participate in at least one window). It is *not* the raw number of (src,dst) edges created.
@@
 ## Spatial metrics (optional)
@@
 It prefers the frame from the most downstream `OutputLayer2D`; if no non‑zero output exists, it falls back to the input frame.
+
+### Even kernels & “same” padding – center rule
+
+When `padding="same"` and the kernel has an **even** size (e.g., `2×2`, `4×4`), the “center” of a window is defined by **flooring** the midpoint:
+
+- center row = `r0 + kh // 2`
+- center col = `c0 + kw // 2`
+
+These indices are then **clamped** to image bounds: `row ∈ [0, H-1]`, `col ∈ [0, W-1]`. For `"valid"` padding the same center rule applies within each valid window.
+
+### C++ parity notes
+
+`Region::connectLayersWindowed` implements the deterministic mapping for `InputLayer2D → OutputLayer2D`. For non‑`OutputLayer2D` destinations it currently connects each participating source pixel to **all** destination neurons (deterministic fan‑out). A future revision may add a selective 2D context fan‑out similar to Python’s `propagate_from_2d`.
```

### 2) src/cpp/Region.cpp — implement deterministic windowed wiring

```diff
--- a/src/cpp/Region.cpp
+++ b/src/cpp/Region.cpp
@@
-#include <random>
+#include <random>
+#include <unordered_set>
+#include <algorithm>
+#include <cctype>
+#include "InputLayer2D.h"
+#include "OutputLayer2D.h"
@@
-int Region::connectLayersWindowed(int sourceIndex, int destIndex,
-                                  int kernelH, int kernelW,
-                                  int strideH, int strideW,
-                                  const std::string& padding,
-                                  bool feedback) {
-    // Minimal parity stub: prefer to wire via Tract deterministically in a future pass.
-    (void)sourceIndex; (void)destIndex; (void)kernelH; (void)kernelW;
-    (void)strideH; (void)strideW; (void)padding; (void)feedback;
-    return 0;
-}
+int Region::connectLayersWindowed(int sourceIndex, int destIndex,
+                                  int kernelH, int kernelW,
+                                  int strideH, int strideW,
+                                  const std::string& padding,
+                                  bool feedback) {
+    if (sourceIndex < 0 || sourceIndex >= static_cast<int>(layers.size()))
+        throw std::out_of_range("connectLayersWindowed: sourceIndex out of range");
+    if (destIndex < 0 || destIndex >= static_cast<int>(layers.size()))
+        throw std::out_of_range("connectLayersWindowed: destIndex out of range");
+
+    // Require InputLayer2D as the source
+    auto src2d = dynamic_cast<InputLayer2D*>(layers[sourceIndex].get());
+    if (!src2d) throw std::invalid_argument("connectLayersWindowed: source must be InputLayer2D");
+
+    // Image shape and params
+    const int H = src2d->height;
+    const int W = src2d->width;
+    const int kh = kernelH, kw = kernelW;
+    const int sh = std::max(1, strideH);
+    const int sw = std::max(1, strideW);
+    std::string pad = padding;
+    std::transform(pad.begin(), pad.end(), pad.begin(), [](unsigned char ch){ return static_cast<char>(std::tolower(ch)); });
+
+    // Enumerate window origins (top-left) for 'valid' or 'same' padding
+    std::vector<std::pair<int,int>> origins;
+    if (pad == "same") {
+        const int pr = std::max(0, (kh - 1) / 2);
+        const int pc = std::max(0, (kw - 1) / 2);
+        const int r0 = -pr, c0 = -pc;
+        for (int r = r0; r + kh <= H + pr + pr; r += sh) {
+            for (int c = c0; c + kw <= W + pc + pc; c += sw) {
+                origins.emplace_back(r, c);
+            }
+        }
+    } else {
+        for (int r = 0; r + kh <= H; r += sh) {
+            for (int c = 0; c + kw <= W; c += sw) {
+                origins.emplace_back(r, c);
+            }
+        }
+    }
+
+    // Build allowed set of participating source indices
+    std::unordered_set<int> allowed;
+    auto& srcNeurons = layers[sourceIndex]->getNeurons();
+    auto& dstNeurons = layers[destIndex]->getNeurons();
+    const bool destIsOut2D = (dynamic_cast<OutputLayer2D*>(layers[destIndex].get()) != nullptr);
+
+    if (destIsOut2D) {
+        // Deterministic mapping: window → center output neuron
+        // Center selection for even kernels uses floor (kh//2, kw//2), then clamp to bounds.
+        std::unordered_set<long long> made; // dedup (srcIdx, centerIdx) to avoid duplicate edges
+        for (auto [r0, c0] : origins) {
+            const int rr0 = std::max(0, r0), cc0 = std::max(0, c0);
+            const int rr1 = std::min(H, r0 + kh), cc1 = std::min(W, c0 + kw);
+            if (rr0 >= rr1 || cc0 >= cc1) continue;
+            const int cr = std::min(H - 1, std::max(0, r0 + kh / 2));
+            const int cc = std::min(W - 1, std::max(0, c0 + kw / 2));
+            const int centerIdx = cr * W + cc;
+
+            for (int rr = rr0; rr < rr1; ++rr) {
+                for (int cc2 = cc0; cc2 < cc1; ++cc2) {
+                    const int srcIdx = rr * W + cc2;
+                    allowed.insert(srcIdx);
+                    const long long key = (static_cast<long long>(static_cast<unsigned int>(srcIdx)) << 32)
+                                          ^ static_cast<unsigned int>(centerIdx);
+                    if (made.insert(key).second) {
+                        if (srcIdx >= 0 && srcIdx < static_cast<int>(srcNeurons.size()) &&
+                            centerIdx >= 0 && centerIdx < static_cast<int>(dstNeurons.size())) {
+                            auto s = srcNeurons[srcIdx];
+                            auto t = dstNeurons[centerIdx];
+                            if (s && t) s->connect(t.get(), feedback);
+                        }
+                    }
+                }
+            }
+        }
+    } else {
+        // Generic case (deterministic fan‑out): connect each participating source pixel
+        // to ALL destination neurons. This is a parity stopgap until selective 2D fan‑out
+        // is added to the C++ Layer API (similar to Python's propagate_from_2d).
+        for (auto [r0, c0] : origins) {
+            const int rr0 = std::max(0, r0), cc0 = std::max(0, c0);
+            const int rr1 = std::min(H, r0 + kh), cc1 = std::min(W, c0 + kw);
+            if (rr0 >= rr1 || cc0 >= cc1) continue;
+            for (int rr = rr0; rr < rr1; ++rr) {
+                for (int cc2 = cc0; cc2 < cc1; ++cc2) {
+                    const int srcIdx = rr * W + cc2;
+                    allowed.insert(srcIdx);
+                }
+            }
+        }
+        for (int srcIdx : allowed) {
+            if (srcIdx < 0 || srcIdx >= static_cast<int>(srcNeurons.size())) continue;
+            auto s = srcNeurons[srcIdx];
+            if (!s) continue;
+            for (auto& t : dstNeurons) {
+                if (t) s->connect(t.get(), feedback);
+            }
+        }
+    }
+
+    // Return the number of unique source subscriptions installed
+    return static_cast<int>(allowed.size());
+}
```

No other files need changes to compile this function. It reuses existing headers/classes and matches the previously declared signature in `Region.h`.

------

## Test Plan

**Python (unchanged behavior):**

- `pytest -q` — should remain **green** (14 passed in your latest run).

- Quick demo still works:

  ```bash
  PYTHONPATH=src/python python src/python/demos/spatial_focus_demo.py
  ```

**C++ (new function only):**

- Build the C++ target(s) as you normally do.

- Manual spot‑check (pseudo‑code using your existing demo harness or a quick main):

  - Create `Region`, add `InputLayer2D (H×W)` and `OutputLayer2D (H×W)`.
  - Call `connectLayersWindowed(src, dst, /*kh=*/3, /*kw=*/3, /*sh=*/2, /*sw=*/2, /*padding=*/"valid")`.
  - Expect return value to equal the count of unique source pixels covered by the sliding windows.
  - Optionally, tick an input frame and ensure delivery occurs (existing tick path).

- (Optional) Enable spatial metrics:

  ```
  GROWNET_ENABLE_SPATIAL_METRICS=1  # and/or region.enableSpatialMetrics=true in code
  ```

  and validate that `tickImage` still reports centroid/bbox/activePixels as before.

------

## Notes / Future follow‑ups (non‑blocking)

- C++ generic destination case currently uses **deterministic fan‑out**. If you later add an API akin to Python’s `Layer.propagate_from_2d`, we can update this to pass row/col context selectively and avoid full fan‑out.
- Python’s 2D slot capacity reuse policy currently uses a **fixed fallback bin** at saturation. If/when we add an LRU or round‑robin policy, we can guard it behind a config flag to preserve current behavior.