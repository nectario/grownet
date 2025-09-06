# CHANGELOG — 2025-09-04

PR-13: Auto‑Growth Parity Finish — Tracts re‑attach grown sources (C++/Java), region‑growth hooks parity, Mojo scaffold confirmed, docs updated.

## Summary
This PR aligns end‑of‑tick auto‑growth mechanics across languages and ensures newly grown source neurons immediately participate in existing inter‑layer tracts.

- C++: Tracts can subscribe newly grown sources; Region re‑attaches sources after layer growth; added a guarded smoke test.
- Java: Tracts expose `attachSourceNeuron`; Region subscribes grown sources; region growth runs after 2D ticks too.
- Mojo: Growth scaffold (`growth_policy.mojo`, `growth_engine.mojo`) already present and hooked at end‑of‑tick — no changes required.
- Docs: Expanded GROWTH.md with a “parity & tract re‑attachment” section.

## Changes by Area
- C++
  - Added `Tract::attachSourceNeuron(int)` that registers a fire hook for the new source.
  - Added `Tract::getSourceLayer()` and `getDestLayer()` accessors.
  - `Region::autowireNewNeuron(...)` now calls `attachSourceNeuron(newIdx)` for any tract that sources from the grown layer.
  - Added `src/cpp/tests/GrowthSmoke.cpp` (compiled when `GROWNET_GROWTH_SMOKE` is defined).

- Java
  - Added `Tract.attachSourceNeuron(int)`; delivers via `destination.propagateFrom(newSourceIndex, amplitude)`.
  - `Region.autowireNewNeuron(...)` calls `attachSourceNeuron(newIdx)` for any tract whose source is the grown layer (a `tracts` list is provided; empty by default).
  - `Region.tick2D(...)` now calls `GrowthEngine.maybeGrow(this, growthPolicy)` after end‑of‑tick, matching scalar/ND parity.

- Mojo
  - No code changes. Existing `growth_policy.mojo` and `growth_engine.mojo` are already called from Region’s end‑of‑tick.

- Docs
  - `docs/GROWTH.md`: Added “Parity & tract re‑attachment” explaining why new sources must be subscribed on windowed tracts.

## Behavior & Compatibility
- No public APIs were removed; all additions are backward compatible.
- Region growth remains off by default (Java/C++), only running when a policy is enabled. Java now evaluates growth after 2D ticks as well.
- Tract re‑attachment ensures new source neurons immediately drive existing windowed projections. If your Java setup doesn’t use Tracts yet, behavior is unchanged until you adopt them.

## Touched Files (selected)
- C++: `src/cpp/Tract.h`, `src/cpp/Tract.cpp`, `src/cpp/Region.cpp`, `src/cpp/tests/GrowthSmoke.cpp`
- Java: `src/java/ai/nektron/grownet/Tract.java`, `src/java/ai/nektron/grownet/Region.java`
- Docs: `docs/GROWTH.md`

## Test Notes
- C++ smoke (optional):
  ```bash
  g++ -std=c++17 -DGROWNET_GROWTH_SMOKE -Isrc/cpp src/cpp/*.cpp src/cpp/tests/GrowthSmoke.cpp -o growth_smoke
  ./growth_smoke
  ```
- Java: If you use Tracts, verify that a newly grown neuron in a source layer triggers deliveries downstream without rewiring.

## Next Steps (optional)
- If adopting Tracts in Java for windowed or tract-style delivery, populate the Region’s `tracts` list so new sources are auto‑subscribed.
- Add a small JUnit test for growth-on-2D parity if you have a test harness.
