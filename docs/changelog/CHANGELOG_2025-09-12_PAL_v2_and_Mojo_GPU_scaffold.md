# GrowNet — PAL v2 (Java Virtual Threads, Python ThreadPool), Mojo GPU scaffold, and C++ naming cleanup

Date: 2025-09-12
Branch: main

## Highlights
- PAL v2 across languages
  - Java: Virtual Threads backend with `Semaphore(maxWorkers)` bound; deterministic submission-order join; requires JDK 21.
  - Python: ThreadPool-backed `parallel_for/map` with deterministic submission-order reduction; respects `ParallelOptions.max_workers`, `tile_size`, and env `GROWNET_PAL_MAX_WORKERS`.
  - C++: OpenMP backend retained; ordered reduction; runtime `maxWorkers` bound; header API now strictly camelCase.
  - Mojo: PAL `device` knob (`"cpu" | "gpu" | "auto"`); GPU path scaffolded for Float64 identity/add/scale maps with CPU fallback; ordered reduction preserved.
- Mojo GPU demo added: shows CPU vs GPU-path (guarded) parity for identity/add/scale kernels.
- C++ naming cleanup: enforce camelCase/PascalCase across PAL and TopographicWiring; removed legacy snake_case alias in RegionMetrics.
- Project memory updated to document PAL v2, runtime knobs, tests and demos.

## Files Added
- `src/mojo/pal/gpu_impl.mojo` — placeholder GPU mapping helpers (identity/add/scale); ready to be replaced with real kernels.
- `src/mojo/tests/pal_gpu_map_demo.mojo` — demo exercising PAL with device knob and three mapping cases.
- `src/java/tests/ai/nektron/grownet/tests/PalDeterminismTest.java` — validates PAL determinism across worker counts.

## Files Modified (selected)
- Python PAL
  - `src/python/pal/api.py` — ThreadPool executor, canonical tiling + submission-order reduction; env `GROWNET_PAL_MAX_WORKERS`.
- Java PAL and fixes
  - `src/java/ai/nektron/grownet/pal/PAL.java` — Virtual Threads; bounded by `maxWorkers`; ordered join.
  - Minor compile fixes in Region windowed wiring local vars, PalDemo cast; TopographicWiring registry reference; tests’ var names and typed lambdas.
- C++ PAL & naming cleanup
  - `src/cpp/include/grownet/pal/Pal.h` — ParallelOptions fields renamed to camelCase (`maxWorkers`, `tileSize`, `vectorizationEnabled`); `parallelFor`/`parallelMap` names; ordered reduction unchanged.
  - `src/cpp/tests/pal_determinism_test.cpp` — updated to new names.
  - `src/cpp/include/TopographicWiring.h` + `src/cpp/src/TopographicWiring.cpp` + demos/tests — fields renamed to camelCase (`kernelH`, `strideH`, `weightMode`, etc.).
  - `src/cpp/Region.h` — removed `delivered_events` alias; use `deliveredEvents` only.
  - `src/cpp/Region.cpp` — minor helper rename `packU32Pair`.
- Mojo PAL
  - `src/mojo/pal/pal.mojo` — PAL device routing; specialized Float64 `gpu_parallel_map` with kernel probes; CPU fallback preserved.
- Project memory
  - `docs/PROJECT_MEMORY.md` — documented PAL v2, runtime knobs, tests/demos, Mojo GPU scaffold and open items.

## Behavior / Parity Notes
- Determinism preserved in all PAL backends by design: stable tiling + submission-order reduction; counter-based RNG unchanged.
- Java PAL requires **JDK 21** (`Executors.newVirtualThreadPerTaskExecutor()`).
- Mojo GPU path is guarded; currently returns CPU results with the correct shape/order. Real kernels (DeviceContext + device buffers + kernel launch) can be dropped into `gpu_impl.mojo` without changing the public API.
- C++ code now adheres to camelCase/PascalCase in public headers; update any external users accordingly.

## Dev UX
- Python
  - `opts = ParallelOptions(max_workers=8, tile_size=4096)`
  - `result = parallel_map(domain, kernel, reducer, opts)`
  - Or `export GROWNET_PAL_MAX_WORKERS=8`
- Java
  - `ParallelOptions opts = new ParallelOptions(); opts.maxWorkers = 8; opts.tileSize = 4096;`
  - `PAL.parallelMap(domain, kernel, reduceInOrder, opts);`
- C++
  - Build with `-DGROWNET_WITH_OPENMP=ON`; limit with `ParallelOptions{.maxWorkers = N}` or `OMP_NUM_THREADS`.
- Mojo
  - `var opts = ParallelOptions(); opts.device = "gpu"` (GPU path guarded; CPU fallback otherwise).
  - Run demo: `mojo run src/mojo/tests/pal_gpu_map_demo.mojo`

## Follow-ups
- Wire real Mojo GPU kernels using DeviceContext and explicit thread/block/grid layouts for identity/add/scale; enable guarded detection in `gpu_available()`.
- Optionally add Python/Java PAL determinism tests mirroring C++/Java coverage.
- Consider forwarding shims for legacy C++ PAL names if external users depend on them (currently updated in-repo).

