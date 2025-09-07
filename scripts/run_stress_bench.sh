#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

PY_HD="N/A"; PY_RET="N/A"
JAVA_HD="N/A"; JAVA_RET="N/A"
CPP_HD="N/A"; CPP_RET="N/A"
MOJO_HD="N/A"; MOJO_RET="N/A"

say() { echo -e "\033[1;34m[bench]\033[0m $*"; }

extract_ms() {
  # Extract the first integer/float before ' ms'
  sed -n 's/.*took ~\([0-9.][0-9.]*\) ms.*/\1/p' | head -n1
}

run_python() {
  say "Python: HD image tick"
  if command -v pytest >/dev/null 2>&1; then
    local out
    out=$(pytest -q src/python/tests/test_stress_hd_image.py -s 2>/dev/null || true)
    echo "$out" | grep "\[PYTHON\]" || true
    local v
    v=$(echo "$out" | extract_ms)
    if [[ -n "$v" ]]; then PY_HD="$v"; fi

    say "Python: Retina (Topographic) HD image tick"
    out=$(pytest -q src/python/tests/test_stress_retina_hd_image.py -s 2>/dev/null || true)
    echo "$out" | grep "\[PYTHON\]" || true
    v=$(echo "$out" | extract_ms)
    if [[ -n "$v" ]]; then PY_RET="$v"; fi
  else
    say "pytest not found; skipping Python"
  fi
}

run_java() {
  if ! command -v mvn >/dev/null 2>&1; then
    say "mvn not found; skipping Java"
    return
  fi
  say "Java: HD image tick"
  local out
  out=$(mvn -q -Dtest=ai.nektron.grownet.tests.StressHDImageTickTest test || true)
  echo "$out" | grep "\[JAVA\]" || true
  local v
  v=$(echo "$out" | extract_ms)
  if [[ -n "$v" ]]; then JAVA_HD="$v"; fi

  say "Java: Retina (Topographic) HD image tick"
  out=$(mvn -q -Dtest=ai.nektron.grownet.tests.StressRetinaHDImageTickTest test || true)
  echo "$out" | grep "\[JAVA\]" || true
  v=$(echo "$out" | extract_ms)
  if [[ -n "$v" ]]; then JAVA_RET="$v"; fi
}

run_cpp() {
  if ! command -v cmake >/dev/null 2>&1; then
    say "cmake not found; skipping C++"
    return
  fi
  say "C++: building tests"
  cmake -S . -B build -G "Unix Makefiles" >/dev/null
  cmake --build build -j >/dev/null

  say "C++: HD image tick"
  local out
  out=$(ctest --test-dir build -R "StressHDImageTick" --output-on-failure || true)
  echo "$out" | grep "\[C\+\+\]" || true
  local v
  v=$(echo "$out" | extract_ms)
  if [[ -n "$v" ]]; then CPP_HD="$v"; fi

  say "C++: Retina (Topographic) HD image tick"
  out=$(ctest --test-dir build -R "StressRetinaHDImageTick" --output-on-failure || true)
  echo "$out" | grep "\[C\+\+\]" || true
  v=$(echo "$out" | extract_ms)
  if [[ -n "$v" ]]; then CPP_RET="$v"; fi
}

run_mojo() {
  if ! command -v mojo >/dev/null 2>&1; then
    say "mojo not found; skipping Mojo"
    return
  fi
  say "Mojo: HD image tick (wall time)"
  # Warm-up once
  mojo run src/mojo/tests/stress_hd_image.mojo >/dev/null 2>&1 || true
  local t0=$(date +%s%3N)
  mojo run src/mojo/tests/stress_hd_image.mojo >/dev/null 2>&1 || true
  local t1=$(date +%s%3N)
  MOJO_HD=$((t1 - t0))

  say "Mojo: Retina (Topographic) HD image tick (wall time)"
  mojo run src/mojo/tests/stress_retina_hd_image.mojo >/dev/null 2>&1 || true
  t0=$(date +%s%3N)
  mojo run src/mojo/tests/stress_retina_hd_image.mojo >/dev/null 2>&1 || true
  t1=$(date +%s%3N)
  MOJO_RET=$((t1 - t0))
}

run_python
run_java
run_cpp
run_mojo

echo
printf "%-8s | %12s | %12s\n" "Language" "HD 1920x1080" "Retina HD"
printf "%-8s-+-%12s-+-%12s\n" "--------" "------------" "------------"
printf "%-8s | %10s ms | %10s ms\n" "Python" "$PY_HD" "$PY_RET"
printf "%-8s | %10s ms | %10s ms\n" "Java" "$JAVA_HD" "$JAVA_RET"
printf "%-8s | %10s ms | %10s ms\n" "C++" "$CPP_HD" "$CPP_RET"
printf "%-8s | %10s ms | %10s ms\n" "Mojo" "$MOJO_HD" "$MOJO_RET"

echo
say "Done. Higher numbers = slower for this coarse benchmark."

