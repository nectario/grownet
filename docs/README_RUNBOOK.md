
# GrowNet – Tests for OR-Trigger and 2D Unfreeze One-Shot (C++/Mojo)

This bundle contains:
- `tests/slot_unfreeze_2d_prefer_once_test.cpp`: C++ GTest for 2D `unfreeze_last_slot()` one-shot reuse.
- `tests/region_growth_or_trigger_test.cpp`: C++ GTest for Region OR-trigger and the one-growth-per-tick invariant.
- `src/mojo/tests/region_growth_or_trigger_test.mojo`: Mojo test for the same invariant.
- `demos/configs/growth_or_trigger_demo.json`: Example config enabling OR-trigger at 25% (demo-only; library defaults remain conservative).

## Integrate (ADAPT notes inline in files)
- Update include paths and method names where marked `ADAPT` to match your tree.
- Ensure your Region tick calls `get_current_step()` on the Region bus (Mojo/C++ parity).
- Expose test-time accessors if needed (e.g., `getLastSlotId()` for C++).

## Build & Run

### C++
```bash
cmake -S . -B build -DCMAKE_BUILD_TYPE=RelWithDebInfo
cmake --build build -j
ctest --test-dir build --output-on-failure
```

### Mojo (adjust to your harness)
```bash
mojo run src/mojo/tests/region_growth_or_trigger_test.mojo
```

### Python sanity (unchanged behavior)
```bash
pytest -q
```

### Style gates
```bash
pre-commit run --all-files
```

## PASS Criteria
- New tests pass.
- Existing growth/windowed wiring tests remain green.
- No linter failures (short-identifier guard, no leading underscores on public names, snake_case in Python/Mojo).
