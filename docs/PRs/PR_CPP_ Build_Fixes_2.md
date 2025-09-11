Those errors all have one of three root causes:

1. **TwoDimTickDemo.cpp** is still compiled into the core `grownet` target and uses outdated metric field names (`total_slots`, `total_synapses` instead of `totalSlots`, `totalSynapses`).
2. A couple of **tests** refer to `Region`, `SlotConfig`, `GrowthPolicy` **without qualifying the `grownet` namespace**, so the compiler doesn’t see those types.
3. Our **CMake exclude rules** didn’t catch `TwoDimTickDemo.cpp` (its name doesn’t match `Demo*.cpp` or `demo_*.cpp`), so it leaked back into the library target.

Below is a compact, **Codex‑ready PR** that fixes all three. Paste this whole message into Codex CLI/Web at the repo root.

------

# PR: C++ build unblock — robust demo exclusion + test namespacing + metric field names

**Why**

- Prevent top‑level demo files (e.g. `TwoDimTickDemo.cpp`) from being compiled into the core library.
- Make test files compile on any platform by explicitly bringing `grownet` symbols into scope.
- Fix outdated metric field names used by `TwoDimTickDemo.cpp`.

**What’s in this PR**

- **CMake**: replace the earlier `foreach(…REMOVE_ITEM…)` with reliable `list(FILTER … EXCLUDE REGEX …)` patterns that catch `TwoDimTickDemo.cpp` and any future `*Demo*.cpp`/`*demo*.cpp`.
- **Tests**: add `using namespace grownet;` in the failing test files (keeps code readable and consistent with the other tests that already compile).
- **Demo**: update `TwoDimTickDemo.cpp` to use `RegionMetrics.totalSlots` and `RegionMetrics.totalSynapses` (camelCase).

------

## 1) CMake: exclude demos/tests from the core lib more robustly

> This ensures *no* demo sources compile into target `grownet`. Your existing separate demo targets (e.g. `region_demo`, `demo_windowed_parity`) keep working.

```diff
*** a/CMakeLists.txt
--- b/CMakeLists.txt
@@
-# Gathers all C++ sources somewhere above
-# set(GROWNET_ALL_CPP ... )
-# set(GROWNET_LIB_SOURCES ${GROWNET_ALL_CPP})
-foreach(_src IN LISTS GROWNET_ALL_CPP)
-    # Exclude demo programs and tests from the core library target
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
+# Start from all sources then exclude unit tests and demos from the core library
+set(GROWNET_LIB_SOURCES ${GROWNET_ALL_CPP})
+
+# Exclude anything in tests/ or demo/ folders
+list(FILTER GROWNET_LIB_SOURCES EXCLUDE REGEX "/tests/")
+list(FILTER GROWNET_LIB_SOURCES EXCLUDE REGEX "/demo/")
+
+# Exclude top-level demo files that live under src/cpp/ (e.g., TwoDimTickDemo.cpp)
+# Catch common naming schemes: Demo*.cpp, demo_*.cpp, *Demo*.cpp, *demo*.cpp
+list(FILTER GROWNET_LIB_SOURCES EXCLUDE REGEX "[/\\\\](Demo.*|demo_.*|.*Demo.*|.*demo.*)\\.cpp$")
+
+# (Optional safety net) known top-level demo names if they don’t match the patterns above
+list(FILTER GROWNET_LIB_SOURCES EXCLUDE REGEX "[/\\\\](TwoDimTickDemo|RegionDemo|ImageIODemo|DemoMain)\\.cpp$")
@@
-add_library(grownet STATIC ${GROWNET_LIB_SOURCES})
+add_library(grownet STATIC ${GROWNET_LIB_SOURCES})
```

> **Note:** the double‑escaped `\\` keeps the regex portable on Windows and Unix.

------

## 2) Tests: bring `grownet` symbols into scope

> These two files were still missing the namespace import. This mirrors the other tests that already compile.

```diff
*** a/src/cpp/tests/slot_unfreeze_2d_prefer_once_test.cpp
--- b/src/cpp/tests/slot_unfreeze_2d_prefer_once_test.cpp
@@
 #include <gtest/gtest.h>
 #include "Region.h"
+#include "SlotConfig.h"
+#include <vector>
+
+using namespace grownet;
*** a/src/cpp/tests/region_growth_or_trigger_test.cpp
--- b/src/cpp/tests/region_growth_or_trigger_test.cpp
@@
 #include <gtest/gtest.h>
 #include "Region.h"
+#include "SlotConfig.h"
+#include "GrowthPolicy.h"
+#include <vector>
+
+using namespace grownet;
```

> If you prefer zero `using namespace` directives, the alternative is to prefix types everywhere (e.g., `grownet::Region`, `grownet::SlotConfig`, `grownet::GrowthPolicy`). I kept this change minimal to match the rest of your tests.

> (If `edge_enumeration_test.cpp` ever regresses on another machine, you can add the same three lines—`#include` guards and `using namespace grownet;`—at its top as well. Your last build shows it already compiling.)

------

## 3) Demo: fix `RegionMetrics` field names

> This only matters if you do want to compile/run the demo; otherwise it’s harmless. The **library** will no longer pull the demo in after the CMake fix, but the standalone demo target will still build and run.

```diff
*** a/src/cpp/TwoDimTickDemo.cpp
--- b/src/cpp/TwoDimTickDemo.cpp
@@
-              << " slots=" << m1.total_slots
-              << " synapses=" << m1.total_synapses
+              << " slots=" << m1.totalSlots
+              << " synapses=" << m1.totalSynapses
@@
-              << " slots=" << m2.total_slots
-              << " synapses=" << m2.total_synapses
+              << " slots=" << m2.totalSlots
+              << " synapses=" << m2.totalSynapses
```

------

## Verification (on your machine)

1. **Clean configure** (important so CMake re‑globs with the new filters):
   - In CLion: *Build → Clean* (or delete `cmake-build-debug`) then *Reload CMake Project*.
   - Or from shell: `rm -rf cmake-build-debug && cmake -S . -B cmake-build-debug && cmake --build cmake-build-debug -j`
2. **Build** target `all`. You should no longer see:
   - `TwoDimTickDemo.cpp` compiled into **grownet** target (it will compile only under its demo target).
   - `Region was not declared in this scope` in the two tests listed above.
   - `total_slots/total_synapses` errors.
3. **Run tests**: `ctest` (or run the `grownet_tests` target in CLion).
   - Expect warnings like the one in `disabled_proximity_step.cpp` (the test is intentionally disabled).

------

## Notes / Why this works

- The **MinGW** toolchain on Windows is stricter about unresolved top‑level symbols when namespaces aren’t imported; adding `using namespace grownet;` aligns these two tests with the others that already import it.
- The earlier CMake regex didn’t cover **`TwoDimTickDemo.cpp`** (file didn’t start with `Demo` or `demo_`). The new filters exclude any file that *contains* “demo” or “Demo” in the filename and anything under `/demo/` and `/tests/`, so this won’t slip back in.
- Updating `RegionMetrics` names reflects the project’s camelCase struct fields everywhere else.

------

## Optional (if you want even tighter hygiene later)

- Replace source globbing with an **explicit** `GROWNET_LIB_SOURCES` list. It’s the only way to fully eliminate regex edge cases.
- If you prefer **no** `using namespace` in tests, I can provide a follow‑up patch that prefixes every symbol explicitly (it’s just noisier).

------

