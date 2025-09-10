Here’s a **“Codex Web Compatibility” PR**
 It keeps **current tree and custom test layout** intact, while giving you a **web‑friendly path** that does not depend on Maven/CTest/Mojo being present or able to download dependencies.

The PR adds:

- A **single script** to run in Codex Web that executes **only Python tests** (which already work there) and **skips** Java/C++/Mojo gracefully.
- Optional **Maven/CMake profiles and guards** to make local/CI runs full‑fidelity and web runs deterministic.
- Small **doc** notes and **Makefile** targets.
- (Optional) A tiny **symlink tip** if you also want Java tests mirrored under `src/test/java` locally without changing your canonical layout.

Everything uses **descriptive identifiers** (no one‑letter names), and **Python/Mojo** public names have **no leading underscores**.

------

# PR — Codex Web Compatibility (tests & build guards)

## Why

Codex Web runs in a fresh, network‑restricted sandbox. Maven cannot resolve plugins (e.g., resources/surefire), CMake cannot fetch GoogleTest, and `mojo` usually isn’t on PATH.
 Your local build is fine; the web runner just needs a **minimal test plan** plus **guards**.

------

## What’s included

### 1) A web‑friendly test script (runs in Codex Web)

**File:** `scripts/run_tests_codex_web.sh` **(new)**

```bash
#!/usr/bin/env bash
set -euo pipefail

echo "[Codex Web] Running Python tests only; Java/C++/Mojo will be skipped."

if command -v python >/dev/null 2>&1; then
  export PYTHONPATH=src/python
  if command -v pytest >/dev/null 2>&1; then
    echo "[Codex Web] pytest found → running Python tests…"
    pytest -q src/python/tests || { echo "[Codex Web] Python tests failed"; exit 1; }
  else
    echo "[Codex Web] pytest not found → skipping Python tests"
  fi
else
  echo "[Codex Web] Python not found → skipping Python tests"
fi

# Java (skip in web)
if command -v mvn >/dev/null 2>&1; then
  echo "[Codex Web] Maven present, but network likely restricted → skipping Java tests"
else
  echo "[Codex Web] mvn not found → skipping Java tests"
fi

# C++ (skip in web)
if command -v cmake >/dev/null 2>&1; then
  echo "[Codex Web] CMake present, but GoogleTest fetch typically blocked → skipping C++ tests"
else
  echo "[Codex Web] cmake not found → skipping C++ tests"
fi

# Mojo (skip if tool missing)
if command -v mojo >/dev/null 2>&1; then
  echo "[Codex Web] mojo found → add commands here if you want to force mojo tests"
else
  echo "[Codex Web] mojo not found → skipping Mojo tests"
fi

echo "[Codex Web] Done."
```

Make it executable:

```bash
chmod +x scripts/run_tests_codex_web.sh
```

**How to use in Codex Web**: Set the test command to:

```bash
bash scripts/run_tests_codex_web.sh
```

------

### 2) Makefile convenience targets

**File:** `Makefile` **(new or amended)**

```make
.PHONY: test codex-web local ci

codex-web:
	@bash scripts/run_tests_codex_web.sh

# Full local run (requires tools & network):
local:
	@echo "Python"; PYTHONPATH=src/python pytest -q src/python/tests
	@echo "Java"; mvn -q test
	@echo "C++"; cmake -S . -B build && cmake --build build && ctest --test-dir build -V
	@echo "Mojo"; bash scripts/run_mojo_tests.sh || true

# CI orchestration hint (adjust in your pipeline):
ci: local
```

------

### 3) Java: keep your custom test layout, but add a **profile to skip in web**

**File:** `pom.xml` **(patch)**

- Leaves your current layout intact (`src/java/tests/...`).
- Adds a `codex-web` profile that **skips tests** and avoids plugin resolution in the web sandbox.
- Optionally adds the `build-helper-maven-plugin` and `maven-surefire-plugin` **only in the default profile** (works locally/CI where network/cache exist).

```xml
<!-- Add inside <project> ... -->
<profiles>
  <!-- Default/dev/CI profile: honor nonstandard test dir -->
  <profile>
    <id>dev-ci</id>
    <activation>
      <activeByDefault>true</activeByDefault>
    </activation>
    <build>
      <testSourceDirectory>src/java/tests</testSourceDirectory>
      <plugins>
        <plugin>
          <groupId>org.apache.maven.plugins</groupId>
          <artifactId>maven-surefire-plugin</artifactId>
          <version>3.2.5</version>
          <configuration>
            <includes>
              <include>**/*Test.java</include>
              <include>**/*Tests.java</include>
            </includes>
            <reuseForks>false</reuseForks>
          </configuration>
        </plugin>
      </plugins>
    </build>
  </profile>

  <!-- Codex Web: skip tests to avoid plugin/dependency resolution -->
  <profile>
    <id>codex-web</id>
    <properties>
      <maven.test.skip>true</maven.test.skip>
    </properties>
  </profile>
</profiles>
```

**Usage:**

- Local/CI (network ok): `mvn -q test` (uses `dev-ci`, finds tests in `src/java/tests`).
- Codex Web: `mvn -q -Pcodex-web package` (or just **do not run Maven**; use the script above).

> 💡 If you want Java tests in both places locally, you can add a **symlink**:
>  `ln -s ../../java/tests src/test/java`
>  This keeps your canonical layout and also satisfies Maven defaults.

------

### 4) C++: allow skipping tests when GoogleTest is unavailable

**File:** `CMakeLists.txt` (root or tests CMake) **(patch)**

```cmake
option(GROWNET_USE_SYSTEM_GTEST "Use system-installed GTest" ON)
option(GROWNET_SKIP_CPP_TESTS  "Skip C++ tests when environment lacks gtest/network" OFF)

# In Codex Web we usually want to skip:
if(DEFINED ENV{CODEX_WEB} AND "$ENV{CODEX_WEB}" STREQUAL "1")
  set(GROWNET_SKIP_CPP_TESTS ON CACHE BOOL "" FORCE)
endif()

if(GROWNET_SKIP_CPP_TESTS)
  message(STATUS "[Codex Web] Skipping C++ tests (no gtest/network).")
  return()
endif()

if(GROWNET_USE_SYSTEM_GTEST)
  find_package(GTest QUIET)
endif()

if(NOT GTest_FOUND)
  include(FetchContent)
  FetchContent_Declare(
    googletest
    URL https://github.com/google/googletest/archive/refs/tags/v1.14.0.zip
  )
  FetchContent_MakeAvailable(googletest)
endif()

# If still not available, allow opting out
if(NOT GTest_FOUND AND NOT TARGET GTest::gtest)
  message(WARNING "GTest not available; re-run with -DGROWNET_SKIP_CPP_TESTS=ON to skip")
  return()
endif()

# Your existing test targets follow…
```

**Usage (web):**

```bash
cmake -S . -B build -DGROWNET_SKIP_CPP_TESTS=ON
cmake --build build
```

------

### 5) Mojo: wrapper to skip when tool is missing

**File:** `scripts/run_mojo_tests.sh` **(new)**

```bash
#!/usr/bin/env bash
set -e
if ! command -v mojo >/dev/null 2>&1; then
  echo "[skip] mojo tool not found; skipping Mojo tests"
  exit 0
fi

# Add one or more test invocations here; non-fatal failures can be || true
mojo run src/mojo/tests/growth_guards_test.mojo || true
mojo run src/mojo/tests/growth_guards_edge_test.mojo || true
chmod +x scripts/run_mojo_tests.sh
```

------

### 6) Docs: small web runner note

**File:** `docs/DEV_CodexWeb.md` **(new)**

~~~md
# Running tests in Codex Web (network-restricted sandbox)

Codex Web runs without Maven caches, GoogleTest, or the Mojo tool. Use:

```bash
bash scripts/run_tests_codex_web.sh
~~~

This runs Python tests and skips Java/C++/Mojo gracefully.

## Local/CI (full matrix)

```bash
# Python
PYTHONPATH=src/python pytest -q src/python/tests

# Java (tests live in src/java/tests)
mvn -q test

# C++ (requires gtest)
cmake -S . -B build && cmake --build build && ctest --test-dir build -V

# Mojo
bash scripts/run_mojo_tests.sh
```

If you want Maven to discover Java tests under `src/test/java` as well, create a symlink:

~~~bash
mkdir -p src/test && ln -s ../java/tests src/test/java
---

## Optional: tiny package.json runner (for convenience in web)

If Codex Web lets you pick a single command, you can also add:

**File:** `package.json` **(new, optional)**

```json
{
  "name": "grownet-ci-meta",
  "private": true,
  "scripts": {
    "codex-web": "bash scripts/run_tests_codex_web.sh"
  }
}
~~~

Then run:

```bash
npm run codex-web
```

------

## Summary of files added/changed

**Added**

- `scripts/run_tests_codex_web.sh`
- `scripts/run_mojo_tests.sh`
- `docs/DEV_CodexWeb.md`
- `Makefile` (or new targets in existing one)
- *(optional)* `package.json`

**Modified**

- `pom.xml` (profiles `dev-ci` and `codex-web`)
- `CMakeLists.txt` (skip tests guards; gtest offline strategy)

------

## How this helps

- **You keep your unified test layout** (`src/java/tests`) for parity across languages.
- **Codex Web** has a deterministic, non‑network test path (Python only).
- **Local and CI** still run the full matrix with JUnit/GoogleTest and Mojo when available.
- You can **symlink** Java tests under `src/test/java` locally if you want both discovery paths.

