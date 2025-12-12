# Running tests in Codex Web (network-restricted sandbox)

Codex Web usually lacks Maven caches, GoogleTest, and the Mojo tool. Use the Python-only runner:

```
bash scripts/run_tests_codex_web.sh
```

This runs Python tests and skips Java/C++/Mojo gracefully.

## Local/CI (full matrix)

```
# Python
PYTHONPATH=src/python pytest -q src/python/tests

# Java (tests live in src/java/tests)
mvn -q test

# C++ (requires gtest)
cmake -S . -B build && cmake --build build && ctest --test-dir build -V

# Mojo
bash scripts/run_mojo_tests.sh
```

If you want Maven to also discover Java tests under `src/test/java` locally, you can create a symlink:

```
mkdir -p src/test && ln -s ../java/tests src/test/java
```

## Optional environment variables / switches

- `CODEX_WEB=1` — CMake guards will default to skipping C++ tests (no gtest/network).
- `-DGROWNET_SKIP_CPP_TESTS=ON` — force-skip C++ tests when configuring CMake.
- `-DGROWNET_USE_SYSTEM_GTEST=OFF` — force FetchContent for gtest (requires network).

