# GrowNet — Changelog (2025‑09‑07)

This change set focuses on:
- Optional, deterministic Proximity Autowiring policy (post‑propagation hook)
- Cross‑language test parity (bus decay, frozen slots, one‑growth‑per‑tick, proximity STEP)
- HD (1920×1080) and Retina/Topographic stress tests across all languages
- Java test layout normalization + build fixes
- C++ test integration via CMake + GTest/CTest

---

## Added

- Proximity Autowiring Policy (sidecar; no core type changes)
  - Python: `src/python/policy/proximity_connectivity.py`
  - Java: `src/java/ai/nektron/grownet/policy/{ProximityConfig, DeterministicLayout, SpatialHash, ProximityEngine}.java`
  - Mojo: `src/mojo/policy/proximity_connectivity.mojo`
  - C++: scaffolding (`src/cpp/include/{ProximityConfig.h, DeterministicLayout.h, SpatialHash.h}`, `src/cpp/src/ProximityEngine.cpp`)
  - Integration (Python/Java/Mojo): one‑liner invoked post‑propagation, pre `end_tick()/bus.decay()`

- Cross‑language tests
  - Bus decay (inhibition *= 0.9, modulation = 1.0, step++):
    - Python: `src/python/tests/test_bus_decay.py`
    - Java: `src/java/tests/ai/nektron/grownet/tests/LateralBusDecayTests.java`
    - C++: `src/cpp/tests/lateral_bus_decay_tests.cpp`
    - Mojo: `src/mojo/tests/bus_decay.mojo`
  - Frozen slots (freeze stops adaptation; unfreeze resumes):
    - Python/Java: existing tests (green)
    - Mojo: `src/mojo/tests/frozen_slots.mojo`
  - One‑growth‑per‑tick invariant (Δlayers ≤ 1/tick):
    - Python: `src/python/tests/test_region_one_growth_per_tick.py`
    - Java: `src/java/tests/ai/nektron/grownet/tests/RegionOneGrowthPerTickTests.java`
    - C++: `src/cpp/tests/one_growth_per_tick.cpp`
    - Mojo: `src/mojo/tests/one_growth_per_tick.mojo`
  - Proximity policy (STEP mode: budget + cooldown):
    - Java: `src/java/tests/ai/nektron/grownet/tests/ProximityPolicyTests.java`
    - Python: earlier test present; policy updated for parity
    - Mojo: `src/mojo/tests/proximity_step.mojo` (STEP only)
    - C++: `src/cpp/tests/disabled_proximity_step.cpp` (placeholder until integration is wired)

- HD and Retina/Topographic stress tests
  - HD 1920×1080 single tick:
    - Java: `StressHDImageTickTest.java`
    - Python: `test_stress_hd_image.py`
    - C++: `stress_hd_image_tick.cpp`
    - Mojo: `stress_hd_image.mojo`
  - Retina/Topographic HD single tick (SAME, 7×7, stride 1):
    - Java: `StressRetinaHDImageTickTest.java`
    - Python: `test_stress_retina_hd_image.py`
    - C++: `stress_retina_hd_image_tick.cpp`
    - Mojo: `stress_retina_hd_image.mojo`

- Benchmark runner (one‑shot)
  - `scripts/run_stress_bench.sh` — runs Python/Java/C++/Mojo HD + Retina tests and prints a summary table
  - Documentation: `docs/BENCHMARKS.md` (+ README pointer)

- C++ CMake test target
  - `CMakeLists.txt`: adds GTest/CTest integration, `grownet_tests` target, and `ctest` hookup

---

## Changed / Fixed

- Java Region
  - `bindInput(...)` now accepts an `InputLayer2D` as the edge for 2D tests (parity with Python convenience) and wires it to other bound targets.

- Java Neuron (unfreeze behavior)
  - Tracks the specific frozen slot and prefers it exactly once on unfreeze (instead of just “last slot”), ensuring adaptation resumes on the intended slot.

- Proximity Engine cooldown semantics (parity)
  - Java/Python: mark per‑source attempt time immediately (cooldown applies even if zero edges are added).
  - Java: per‑region per‑step guard — at most one proximity application per region step.

- Java test layout + Maven build fixes
  - Tests moved under `src/java/tests/...` (single location).
  - POM: sets `sourceDirectory=src/java`, `testSourceDirectory=src/java/tests`, excludes `tests/**` from main compile, marks test sources via `build-helper-maven-plugin`.
  - JUnit 5 dependencies added (aggregate `junit-jupiter` + API/engine); IntelliJ resolves after Maven reimport.

- C++ tests
  - Guarded with `GTEST_AVAILABLE` and integrated via CTest; FetchContent downloads GTest when missing.

---

## How to run

- Python
  - `pytest -q` (or run specific files under `src/python/tests/`)

- Java
  - `mvn -q test` (root `pom.xml`)

- C++
  - `cmake -S . -B build && cmake --build build -j && ctest --test-dir build --output-on-failure`

- Mojo
  - `mojo run` for individual tests in `src/mojo/tests/`

- One‑shot benchmark
  - `bash scripts/run_stress_bench.sh`

---

## Notes

- Stress tests print timing instead of enforcing a pass/fail threshold to keep results stable across environments; use relative comparisons on the same machine.
- The C++ proximity policy is scaffolded but not integrated yet; a disabled test is present to maintain parity until it’s wired into `Region`.
- All Java tests (including HD/Retina stress) run green with Maven after reimporting the root POM in IntelliJ.
