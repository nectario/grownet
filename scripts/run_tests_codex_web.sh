#!/usr/bin/env bash
set -euo pipefail

echo "[Codex Web] Running Python tests only; Java/C++/Mojo will be skipped."

# --- Python ---
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

# --- Java ---
if command -v mvn >/dev/null 2>&1; then
  echo "[Codex Web] Maven present, but network likely restricted → skipping Java tests"
else
  echo "[Codex Web] mvn not found → skipping Java tests"
fi

# --- C++ ---
if command -v cmake >/dev/null 2>&1; then
  echo "[Codex Web] CMake present, but GoogleTest fetch typically blocked → skipping C++ tests"
else
  echo "[Codex Web] cmake not found → skipping C++ tests"
fi

# --- Mojo ---
if command -v mojo >/dev/null 2>&1; then
  echo "[Codex Web] mojo found → add commands here if you want to force mojo tests"
else
  echo "[Codex Web] mojo not found → skipping Mojo tests"
fi

echo "[Codex Web] Done."

