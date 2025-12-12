# PR — C++ Build Fixes (CMake filters, demo metrics rename, test namespace cleanup)

**Why:** Your build log shows:

- `TwoDimTickDemo.cpp` referencing `RegionMetrics.total_slots/total_synapses` (old names) → should be `totalSlots/totalSynapses`.
- Several tests failing with `Region was not declared in this scope` because they use `Region` without the `grownet::` namespace.
- Core target `grownet` is still compiling **top‑level** demo files (e.g., `TwoDimTickDemo.cpp`, `ImageIODemo.cpp`, `RegionDemo.cpp`) even though we intended to exclude demos from the library.

This PR fixes all three classes of issues, without touching runtime logic.

------

## 1) CMake — exclude demos & tests from the **core** library target

Make the exclusion robust: filter out **tests**, **demo dir**, and **standalone demo .cpp in root** (`*Demo*.cpp`, `demo_*.cpp`). This stops the core from compiling demo programs, and keeps their compile in their **own** targets only.

```diff
*** a/CMakeLists.txt
--- b/CMakeLists.txt
@@
-# Collect sources
-file(GLOB_RECURSE GROWNET_ALL_CPP CONFIGURE_DEPENDS src/cpp/*.cpp)
-
-set(GROWNET_LIB_SOURCES ${GROWNET_ALL_CPP})
-
-# Previously: only excluded /demo/. Strengthen the filters.
-foreach(_src IN LISTS GROWNET_LIB_SOURCES)
-    if(_src MATCHES "/demo/")
-        list(REMOVE_ITEM GROWNET_LIB_SOURCES "${_src}")
-    elseif(_src MATCHES "/tests/")
-        list(REMOVE_ITEM GROWNET_LIB_SOURCES "${_src}")
-    elseif(_src MATCHES "[/\\]Demo.*\\.cpp$")
-        list(REMOVE_ITEM GROWNET_LIB_SOURCES "${_src}")
-    elseif(_src MATCHES "[/\\]demo_.*\\.cpp$")
-        list(REMOVE_ITEM GROWNET_LIB_SOURCES "${_src}")
-    endif()
-endforeach()
+# Collect sources for the **library** target only
+file(GLOB_RECURSE GROWNET_ALL_CPP CONFIGURE_DEPENDS src/cpp/*.cpp)
+set(GROWNET_LIB_SOURCES ${GROWNET_ALL_CPP})
+
+# Exclude tests and demos from the library
+list(FILTER GROWNET_LIB_SOURCES EXCLUDE REGEX "src/cpp/tests/")
+list(FILTER GROWNET_LIB_SOURCES EXCLUDE REGEX "src/cpp/demo/")
+# Also exclude any top-level demo sources (e.g., TwoDimTickDemo.cpp, RegionDemo.cpp, ImageIODemo.cpp)
+list(FILTER GROWNET_LIB_SOURCES EXCLUDE REGEX "src/cpp/.*[dD]emo.*\\.cpp$")
+list(FILTER GROWNET_LIB_SOURCES EXCLUDE REGEX "src/cpp/demo_.*\\.cpp$")
 
 add_library(grownet STATIC ${GROWNET_LIB_SOURCES})
 target_include_directories(grownet PUBLIC src/cpp src/cpp/include src/cpp/grownet)
```

> **Result:** `TwoDimTickDemo.cpp`, `RegionDemo.cpp`, and `ImageIODemo.cpp` will no longer be compiled into the `grownet` library (which is where your error came from: `CMakeFiles/grownet.dir/src/cpp/TwoDimTickDemo.cpp.obj`). They still build in their dedicated demo targets.

------

## 2) Demo: fix `RegionMetrics` field names in `TwoDimTickDemo.cpp`

The struct uses **camelCase** (`totalSlots`, `totalSynapses`), not `total_slots`, `total_synapses`.

```diff
*** a/src/cpp/TwoDimTickDemo.cpp
--- b/src/cpp/TwoDimTickDemo.cpp
@@ -38,9 +38,9 @@ int main() {
   auto m1 = region.tick("img", 1.0);
   std::cout << "[tick1] events=" << 1
-            << " slots=" << m1.total_slots
-            << " synapses=" << m1.total_synapses
+            << " slots=" << m1.totalSlots
+            << " synapses=" << m1.totalSynapses
             << std::endl;
@@ -49,9 +49,9 @@ int main() {
   auto m2 = region.tick("img", 0.5);
   std::cout << "[tick2] events=" << 1
-            << " slots=" << m2.total_slots
-            << " synapses=" << m2.total_synapses
+            << " slots=" << m2.totalSlots
+            << " synapses=" << m2.totalSynapses
             << std::endl;
 }
```

> **Note:** Even though the CMake filter above removes this file from the library, it still compiles for its own demo target—so fixing the names keeps the demo compiling cleanly in both MSYS2/MinGW and MSVC.

------

## 3) Tests — add `grownet::` namespace or `using` aliases where missing

Your tests are written using `Region`/`SlotConfig`/`GrowthPolicy` without qualification. On some compilers/flags that fails (as in your log). Add explicit `using` statements (lightweight and local to the test file) or prefix with `grownet::`.

### 3.1 `edge_enumeration_test.cpp`

```diff
*** a/src/cpp/tests/edge_enumeration_test.cpp
--- b/src/cpp/tests/edge_enumeration_test.cpp
@@
-#include "Region.h"
+#include "Region.h"
+#include <vector>
+#include <unordered_map>
+#include <utility>
+
+using grownet::Region;
+using grownet::InputLayer2D;
+using grownet::OutputLayer2D;
 
 // ... existing helpers (EdgeMap etc.) ...
 
-static EdgeMap enumerateEdgesOutput2D(Region& region, int src_layer_index, int dst_layer_index) {
+static EdgeMap enumerateEdgesOutput2D(Region& region, int src_layer_index, int dst_layer_index) {
     // body unchanged
 }
@@
-    Region region("dedupe-cpp");
-    int src_index = region.addInput2DLayer(4, 4);
+    Region region("dedupe-cpp");
+    int src_index = region.addInputLayer2D(4, 4);   // ADAPT: correct method name
     int dst_index = region.addOutputLayer2D(4, 4, 0.0);
     // rest unchanged
```

### 3.2 `region_growth_or_trigger_test.cpp`

```diff
*** a/src/cpp/tests/region_growth_or_trigger_test.cpp
--- b/src/cpp/tests/region_growth_or_trigger_test.cpp
@@
-#include "Region.h"
+#include "Region.h"
+#include <vector>
+
+using grownet::Region;
+using grownet::SlotConfig;
+using grownet::GrowthPolicy;
 
-static void drive_tick_with_uniform_frame(Region& region,
+static void drive_tick_with_uniform_frame(Region& region,
                                           int input_layer_index,
                                           int frame_height,
                                           int frame_width,
                                           float active_value) {
     // body unchanged
 }
@@
-    Region region("or_trigger_test"); // ADAPT
+    Region region("or_trigger_test");
     const int frame_height = 4, frame_width = 4;
-    const int input_layer_index = region.addInputLayer2D(frame_height, frame_width); // ADAPT
+    const int input_layer_index = region.addInputLayer2D(frame_height, frame_width);
 
-    SlotConfig slot_config;
+    SlotConfig slot_config;
     slot_config.slotLimit = 1;
 
-    GrowthPolicy growth_policy;
+    GrowthPolicy growth_policy;
     // rest unchanged
```

### 3.3 `slot_unfreeze_2d_prefer_once_test.cpp`

```diff
*** a/src/cpp/tests/slot_unfreeze_2d_prefer_once_test.cpp
--- b/src/cpp/tests/slot_unfreeze_2d_prefer_once_test.cpp
@@
-#include "Region.h"
+#include "Region.h"
+#include <vector>
+
+using grownet::Region;
+using grownet::SlotConfig;
 
-static void drive_tick_with_frame(Region& region,
+static void drive_tick_with_frame(Region& region,
                                   int input_layer_index,
                                   const std::vector<float>& frame_values,
                                   int frame_height,
                                   int frame_width) {
     // body unchanged
 }
@@
-    Region region("unfreeze_2d_test");                  // ADAPT name/api
+    Region region("unfreeze_2d_test");
     const int frame_height = 4, frame_width = 4;
-    const int input_layer_index = region.addInput2DLayer(frame_height, frame_width); // ADAPT
+    const int input_layer_index = region.addInputLayer2D(frame_height, frame_width);
 
-    SlotConfig slot_config;                             // ADAPT ctor/fields
+    SlotConfig slot_config;
     slot_config.growthEnabled = true;
     // rest unchanged
```

> These minimal edits preserve test logic and just make the types resolvable under the `grownet` namespace. They also correct the outdated `addInput2DLayer` identifier.

------

## Build/Run notes

1. **Clean** build dir after applying this PR (CLion: *Build → Clean*, or delete `cmake-build-debug`).
2. Reconfigure (CLion will re‑run CMake).
3. Build `all`. You should see:
   - no attempts to compile the demo `.cpp` files inside the `grownet` library target;
   - `TwoDimTickDemo.cpp` still builds for its own demo target and now references `totalSlots/totalSynapses`;
   - tests compile with `grownet::` types resolved.

------

## Optional (if you want to be extra tidy)

If any remaining test references `addInput2DLayer`, replace with `addInputLayer2D` as above (I updated the two places surfaced by the log). If you prefer **not** to change tests, you can add a tiny compatibility alias in `Region.h`:

```diff
*** a/src/cpp/Region.h
--- b/src/cpp/Region.h
@@
 public:
     int addInputLayer2D(int height, int width, double gain = 1.0, double epsilonFire = 0.0);
+    // Back-compat alias for older tests:
+    inline int addInput2DLayer(int height, int width) { return addInputLayer2D(height, width, 1.0, 0.0); }
```

But the diffs above already modernize the tests, so the alias is optional.

------

## Why these fixes match your errors exactly

- `TwoDimTickDemo.cpp`: your log shows `error: 'struct grownet::RegionMetrics' has no member named 'total_slots'` → rename to `totalSlots`, `totalSynapses`.
- `edge_enumeration_test.cpp` + `region_growth_or_trigger_test.cpp` + `slot_unfreeze_2d_prefer_once_test.cpp`: *“`Region` was not declared in this scope”* and missing helper signatures → add `using grownet::Region;` (and friends), include `<vector>`, and update the two occurrences of the old method name.
- Demos were still being compiled into the **library** target (e.g., `CMakeFiles/grownet.dir/src/cpp/TwoDimTickDemo.cpp.obj`) → strengthened CMake filters to exclude any `*Demo*.cpp` and `demo_*.cpp` under `src/cpp/`, plus `src/cpp/demo/` and `src/cpp/tests/`.

------

If anything else pops up after this (e.g., MSVC vs MinGW dialect quirks), send the next build log and I’ll patch those too.