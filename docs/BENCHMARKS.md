# GrowNet — Cross‑Language Stress Benchmarks

This document explains how to run the cross‑language stress benchmarks that compare the cost of a single HD (1920×1080) 2D tick across Python, Java, C++, and Mojo. It also covers a “Retina / Topographic” case (InputLayer2D → OutputLayer2D with SAME padding and a 7×7 kernel).

The intent is a coarse, apples‑to‑apples comparison of basic 2D processing overhead per language. It is not a microbenchmark of internal loops.

## What’s measured

- HD 1920×1080 input edge only:
  - Bind a 2D input edge for port `img`.
  - Warm‑up tick, then time a single `tick2D`/`tick_image`.
  - Report the elapsed time and assert `deliveredEvents == 1`.

- Retina / Topographic wiring:
  - `InputLayer2D` → `OutputLayer2D` with SAME padding, 7×7 kernel, stride 1.
  - Build deterministic weights (Gaussian) and per‑target normalization.
  - Warm‑up tick, then time a single `tick2D`/`tick_image`.

All tests log timing and avoid strict thresholds to reduce flakiness across machines.

## Prerequisites

- Python: `pytest` in PATH
- Java: Maven (`mvn`) and JDK 21
- C++: `cmake` (and a C++17 compiler); GTest is fetched automatically if missing
- Mojo: `mojo` tool in PATH

## One‑shot driver script

Use the helper script to run everything and summarize times:

```
bash scripts/run_stress_bench.sh
```

It will:
- Run Python and Java stress tests, extracting timing from test output
- Build and run C++ tests via CMake/CTest and capture timing
- Run Mojo tests twice and use wall‑clock timing for the second run
- Print a simple table:

```
Language | HD 1920x1080 | Retina HD
-------- -+ ------------ -+ ------------
Python   |      123 ms   |      456 ms
Java     |       94 ms   |      312 ms
C++      |       55 ms   |      210 ms
Mojo     |      180 ms   |      440 ms
```

> Tip: Run the script multiple times and take the median—JIT warmup (Java) and turbo modes can affect the first run.

## Running individual tests

### Java

```
mvn -q -Dtest=ai.nektron.grownet.tests.StressHDImageTickTest test
mvn -q -Dtest=ai.nektron.grownet.tests.StressRetinaHDImageTickTest test
```

### Python

```
pytest -q src/python/tests/test_stress_hd_image.py -s
pytest -q src/python/tests/test_stress_retina_hd_image.py -s
```

### C++

```
cmake -S . -B build
cmake --build build -j
ctest --test-dir build -R "StressHDImageTick|StressRetinaHDImageTick" --output-on-failure
```

### Mojo

```
mojo run src/mojo/tests/stress_hd_image.mojo
mojo run src/mojo/tests/stress_retina_hd_image.mojo
```

## Interpreting results

- Lower time generally means faster per‑tick 2D processing overhead.
- The Retina case highlights any extra overhead from windowed/center‑mapped wiring and per‑target normalization.
- Absolute times will vary by hardware, OS, kernel, and toolchain; compare **relative** differences on the same machine.

## Troubleshooting

- Python prints nothing
  - Ensure `pytest` is installed and in PATH; re‑run the script.

- Java tests fail to resolve JUnit
  - Reimport Maven; ensure JDK 21 is configured in IntelliJ and for the Maven importer.

- C++ tests not found
  - Check that `cmake` exists and `src/cpp/tests` files are present; reconfigure the build.

- Mojo not found
  - Install `mojo` and ensure it’s on PATH; comment out the Mojo block in the script if not available.

## Where to tweak

- Kernel/padding in Retina tests: change in test files or preset configs.
- Normalization: toggle via `normalizeIncoming` / `normalize_incoming` fields.
- Script parsing: the `extract_ms()` function relies on lines printing `took ~XXX ms`—keep that format in tests for consistency.

