# PAL v1.5 — Parallelism Abstraction Layer

- One API in all languages (`pal.parallel_for`, `pal.parallel_map`, `pal.counter_rng`).
- Deterministic by design (stable domain ordering + ordered reductions).

## Backends
- C++: OpenMP (enabled by default if available)
- Java: Fixed platform executor + Structured Concurrency
- Python: Orchestrates; benefits when compute in native code
- Mojo: CPU tiling now; device switch point for future GPU

## Build
- CMake flag: `-DGROWNET_WITH_OPENMP=ON` (default ON). If OpenMP not found, PAL runs sequentially.
- Java: JDK 21 for `StructuredTaskScope`. If preview/incubator is not available in your build, swap to `invokeAll` on a fixed executor; determinism remains.

## Determinism
- Use `pal.counter_rng(seed, step, draw_kind, layer_index, unit_index, draw_index)` for all probabilistic kernels.
- Reductions merge partials **in worker id order** (or a fixed-shape pairwise tree in a future update).

