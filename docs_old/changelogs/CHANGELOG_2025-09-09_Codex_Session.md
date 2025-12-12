# GrowNet — Codex Session Changelog (Web compatibility + C++ windowed tract + proximity hooks)

Date: $(date)
Branch: main

## Highlights

- Codex Web compatibility: Python-only test runner, Makefile targets, Maven/CMake guards, dev doc.
- C++: Windowed Tract geometry recorded and used for deterministic re-attach on growth; unique-source return preserved.
- Proximity policy: integrated call path with once-per-step guard across tick, tick2D, and tickND.
- Demo: small windowed wiring parity demo printing uniqueSources for common configs.
- Tests: added gtest smoke/coverage for windowed wiring, re-attach, and proximity STEP guard.
- Small cleanup: removed duplicated spatial metrics block in tick2D; descriptive identifiers enforced.

## Files Added

- scripts/run_tests_codex_web.sh — Python-only runner (skips Java/C++/Mojo in Codex Web).
- scripts/run_mojo_tests.sh — Mojo wrapper (skips if tool unavailable).
- Makefile — convenience targets: codex-web, local, ci.
- docs/DEV_CodexWeb.md — how to run in Codex Web and locally.
- src/cpp/include/TractWindowed.h — records windowed geometry (SAME/VALID + stride; center mapping).
- src/cpp/src/TractWindowed.cpp — implementation (dedup (source→center) edges; allowed source set).
- src/cpp/include/ProximityEngine.h — proximity engine interface.
- src/cpp/tests/windowed_wiring_center_test.cpp — verifies unique-source center mapping smoke.
- src/cpp/tests/windowed_reattach_test.cpp — smoke for deterministic re-attach after growth.
- src/cpp/tests/proximity_step_test.cpp — proximity STEP guard smoke test.
- src/cpp/demo/demo_windowed_parity.cpp — prints uniqueSources across several window configs.

## Files Modified

- CMakeLists.txt
  - Added include path `src/cpp/include`.
  - Added options `GROWNET_USE_SYSTEM_GTEST`, `GROWNET_SKIP_CPP_TESTS`.
  - Respect `CODEX_WEB=1` to skip C++ tests.
  - Added demo target `demo_windowed_parity`.
- pom.xml
  - Added `codex-web` profile to skip tests (network-restricted web).
- src/python/tests/conftest.py
  - Fixed loop var name (`p` → `p_var`) when bootstrapping `sys.path`.
- src/cpp/Region.h
  - Recorded `windowedTracts` store; descriptive param names.
  - Proximity config fields + `setProximityConfig(const ProximityConfig&)`.
- src/cpp/Region.cpp
  - Rewrote `connectLayersWindowed(...)` to build/record `TractWindowed`, wire deterministically, and return unique sources.
  - `autowireNewNeuron(...)` re-attaches grown sources to windowed geometry.
  - Proximity pass (once per tick) in `tick(...)`, `tick2D(...)`, and `tickND(...)` (pre endTick/decay).
  - Removed duplicated spatial metrics block in `tick2D(...)`.
- src/cpp/src/ProximityEngine.cpp
  - Implemented `ProximityEngine::Apply(...)` stub; integrated header; kept best-effort semantics.

## Behavior/Parity Notes

- Windowed wiring preserves contract: center rule (floor + clamp) and return value = unique source subscriptions.
- Growth: grown sources are deterministically re-attached based on recorded window geometry.
- Proximity: optional, best‑effort; called once per region step across all tick variants.
- Style: no single/double-character identifiers in new/changed code.

## Dev UX

- Codex Web: run `bash scripts/run_tests_codex_web.sh`.
- Local:
  - Python: `PYTHONPATH=src/python pytest -q src/python/tests`
  - Java: `mvn -q test` (use `-Pcodex-web` to skip in web)
  - C++: `cmake -S . -B build && cmake --build build && ctest --test-dir build -V` (or `-DGROWNET_SKIP_CPP_TESTS=ON`)
  - Mojo: `bash scripts/run_mojo_tests.sh`

