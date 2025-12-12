## PR: Spatial windowed wiring polish (safe size calc, return semantics, Output2D clamp)

**Summary**

- Use `size_t(height) * size_t(width)` for the `allowedMask` allocation (avoids potential signed overflow).
- Document the return value of `connectLayersWindowed`: **count of unique source subscriptions**.
- Add `getHeight()/getWidth()` to `OutputLayer2D` and clamp the computed window center to the **destination** shape before indexing.
- Use a small helper to pack `(srcIdx, centerIdx)` into an **unsigned 64‑bit key** for dedupe.

### Patches

> Codex can apply fuzzy context; exact line numbers are not required.

#### 1) `src/cpp/Region.h` — clarify return semantics in the declaration

```diff
--- a/src/cpp/Region.h
+++ b/src/cpp/Region.h
@@ -73,10 +73,13 @@
-    // Windowed deterministic wiring (spatial focus helper). Returns number of edges created.
+    // Windowed deterministic wiring (spatial focus helper).
+    // Return value: number of UNIQUE source subscriptions (i.e., the count of
+    // distinct source pixels that participate in ≥1 window). It is NOT the raw
+    // number of (src,dst) edges.
     int connectLayersWindowed(int sourceIndex, int destIndex,
                               int kernelH, int kernelW,
                               int strideH=1, int strideW=1,
                               const std::string& padding="valid",
                               bool feedback=false);
```

#### 2) `src/cpp/OutputLayer2D.h` — add shape accessors

```diff
--- a/src/cpp/OutputLayer2D.h
+++ b/src/cpp/OutputLayer2D.h
@@ -24,6 +24,10 @@ class OutputLayer2D : public Layer {
 public:
     OutputLayer2D(int heightPixels, int widthPixels, double smoothing)
         : Layer(0, 0, 0), height(heightPixels), width(widthPixels), frame(heightPixels, std::vector<double>(widthPixels, 0.0)) {
         // ...
     }
+
+    // Accessors used by Region for deterministic windowed wiring
+    int getHeight() const { return height; }
+    int getWidth()  const { return width;  }
```

#### 3) `src/cpp/Region.cpp` — safe mask size, unsigned pack helper, clamp center to dest shape

```diff
--- a/src/cpp/Region.cpp
+++ b/src/cpp/Region.cpp
@@ -1,8 +1,10 @@
 #include <random>
 #include <cstdlib>
+#include <cstdint>
 #include <stdexcept>
 #include <unordered_set>
 #include <algorithm>
@@
+// Helper: pack two 32-bit ints into an unsigned 64-bit key (for dedupe sets).
+static inline unsigned long long pack_u32_pair(int a, int b) {
+    return ((static_cast<unsigned long long>(a) & 0xFFFFFFFFULL) << 32)
+         |  (static_cast<unsigned long long>(b) & 0xFFFFFFFFULL);
+}
@@
-    // Build allowed source set; if dest is OutputLayer2D, connect (src -> center) with dedupe.
-    std::vector<char> allowedMask(static_cast<size_t>(height * width), 0);
+    // Build allowed source set; if dest is OutputLayer2D, connect (src -> center) with dedupe.
+    std::vector<char> allowedMask(static_cast<size_t>(height) * static_cast<size_t>(width), 0);
     auto& srcNeurons = src->getNeurons();
     auto& dstNeurons = layers[destIndex]->getNeurons();
@@
     if (dstOut) {
         std::unordered_set<unsigned long long> made; // dedup (srcIdx, centerIdx)
         for (auto [r0, c0] : origins) {
             const int rr0 = std::max(0, r0), cc0 = std::max(0, c0);
             const int rr1 = std::min(height, r0 + kh), cc1 = std::min(width, c0 + kw);
             if (rr0 >= rr1 || cc0 >= cc1) continue;
-
-            const int cr = std::min(height - 1, std::max(0, r0 + kh / 2));
-            const int cc = std::min(width  - 1, std::max(0, c0 + kw / 2));
-            const int centerIdx = cr * width + cc;
+            // Compute center in source coordinates (floor midpoint), then clamp to DEST shape.
+            const int srcCenterR = std::min(height - 1, std::max(0, r0 + kh / 2));
+            const int srcCenterC = std::min(width  - 1, std::max(0, c0 + kw / 2));
+            const int dstH = dstOut->getHeight();
+            const int dstW = dstOut->getWidth();
+            const int centerR = std::min(dstH - 1, std::max(0, srcCenterR));
+            const int centerC = std::min(dstW - 1, std::max(0, srcCenterC));
+            const int centerIdx = centerR * dstW + centerC;
@@
                 const int srcIdx = rr * width + cc2;
                 allowedMask[srcIdx] = 1;
-
-                const long long key = (static_cast<long long>(srcIdx) << 32)
-                                      | static_cast<unsigned long long>(centerIdx);
-                if (!made.insert(key).second) continue;
+                const unsigned long long key = pack_u32_pair(srcIdx, centerIdx);
+                if (!made.insert(key).second) continue;
 
                 if (srcIdx >= 0 && srcIdx < static_cast<int>(srcNeurons.size()) &&
                     centerIdx >= 0 && centerIdx < static_cast<int>(dstNeurons.size())) {
                     auto s = srcNeurons[srcIdx];
                     auto t = dstNeurons[centerIdx];
                     if (s && t) s->connect(t.get(), feedback);
                 }
```

------

## Why this is safe

- **No behavior change** in the typical equal‑shape case; the center clamp now explicitly respects the destination grid.
- `allowedMask` allocation becomes robust for larger shapes because we multiply in `size_t`.
- The pack helper removes signed/unsigned mixing and documents the intent.

## Test plan

- Rebuild C++ and re‑run the smoke test you already added:

  ```bash
  g++ -std=c++17 -DGROWNET_WINDOWED_WIRING_SMOKE -Isrc/cpp \
      src/cpp/*.cpp src/cpp/tests/WindowedWiringSmoke.cpp -o win_smoke
  ./win_smoke
  ```

- Expected: same **[OK]** lines as before; all cases pass.

