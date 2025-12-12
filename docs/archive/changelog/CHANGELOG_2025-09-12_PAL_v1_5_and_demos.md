# CHANGELOG — 2025-09-12 — PAL v1.5 + Demos + Naming Hygiene

## Added

- Parallelism Abstraction Layer (PAL v1.5)
  - C++: OpenMP-backed `pal::parallel_for/parallel_map` with deterministic, ordered reductions; sequential fallback when OpenMP is unavailable.
  - Java: `ai.nektron.grownet.pal` (ParallelOptions, Domain, PAL) using a fixed platform thread pool + Structured Concurrency for orchestration; stable tiling; ordered merges.
  - Python: PAL façade (`src/python/pal/api.py`) with deterministic sequential fallback; `counter_rng` (SplitMix64-style).
  - Mojo: PAL façade (`src/mojo/pal/pal.mojo`) with CPU tiling; device switch point reserved for GPU.
- PAL demos and tiny example domains
  - Python: `src/python/demos/pal_demo.py` and `src/python/pal/domains.py` (IndexDomain, build_layer_neuron_tiles).
  - Java: `ai.nektron.grownet.pal.PalDemo` and `IndexDomain`.
  - Mojo: `src/mojo/pal_demo.mojo` and `src/mojo/pal/domains.mojo`.
- C++ determinism test: `src/cpp/tests/pal_determinism_test.cpp` verifies identical results across worker counts.
- Docs: `docs/PAL_README.md` quick-start for PAL.

## Changed

- Python Region 2D path: feature-flagged PAL wiring for structural metrics aggregation in `tick_2d`.
  - Set `GROWNET_ENABLE_PAL=1` to aggregate slots/synapses via PAL tiling. Default off; behavior unchanged otherwise.
- Mojo: replaced all `let` declarations with `var` (current toolchain guidance); no behavior change.
- Naming hygiene and style:
  - Removed leading underscores from public/helper names (Python/Mojo/Java), e.g., `mix64`, `GLOBAL_OPTIONS`, `origin_list`.
  - Expanded ambiguous single/double-character locals in demos/tests and a few core spots (kept `i/j` loop indices).

## Fixed / Infrastructure

- CMake: `-DGROWNET_WITH_OPENMP=ON` (default ON). Detects and links OpenMP for `grownet` (and `grownet_tests` when present). Falls back to sequential if not found.
- Java PAL: determinism preserved by tiling in canonical order and merging buckets in submission/worker order.
- Cross-language `counter_rng`: shared SplitMix64-style mixing ensures identical draws given the same inputs.

## Migration / Usage Notes

- No call-site changes are required. PAL is a façade; you can start importing it in new code paths.
- To try the Python 2D metrics PAL integration: `export GROWNET_ENABLE_PAL=1` and run any 2D demo/test.
- Building C++ with OpenMP is recommended for performance: `cmake -DGROWNET_WITH_OPENMP=ON ..`.
- Java PAL currently uses JDK 21 Structured Concurrency (`StructuredTaskScope`). If your build cannot enable incubator/preview, swap to `ExecutorService.invokeAll` (determinism remains).

## Determinism Guarantees

- Domains enumerate in a stable order; reductions are ordered (worker 0..N–1) to ensure identical results regardless of worker count.
- All probabilistic code should use `pal.counter_rng(seed, step, draw_kind, layer_index, unit_index, draw_index)`—no shared mutable RNG.

## What’s next (optional)

- Wire PAL into Phase‑A/Phase‑B kernels under the same feature flag and extend determinism gates to those paths.
- Add a fixed-shape pairwise tree reduction helper for numerically friendlier merges (still deterministic).
- Mojo GPU kernels behind `device="auto"` with host-side ordered reductions for identical results.

