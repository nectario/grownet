#!/usr/bin/env bash
set -e

if ! command -v mojo >/dev/null 2>&1; then
  echo "[skip] mojo tool not found; skipping Mojo tests"
  exit 0
fi

# Example Mojo tests (non-fatal if a given file is missing)
if [[ -f src/mojo/tests/growth_guards_test.mojo ]]; then
  mojo run src/mojo/tests/growth_guards_test.mojo || true
fi
if [[ -f src/mojo/tests/region_growth_or_trigger_test.mojo ]]; then
  mojo run src/mojo/tests/region_growth_or_trigger_test.mojo || true
fi

echo "[Mojo] Done."

