# PR: V4 (Python) temporal-focus compatibility & testing shim — ports-as-edges semantics preserved

## Motivation
Phase A introduced temporal focus work and a V4 clarification: *ports are edges*. Tests and demos still mixed older assumptions (e.g., counting bound layers as delivered events, camelCase vs snake_case, `slots()` vs `slots` dict). This PR aligns Python with V4 while providing a scoped compatibility path for legacy tests—without changing core semantics.

## Summary of changes (already committed)
- **Testing bootstrap**
  - `src/python/tests/conftest.py`: injects repo root and `src/python/` into `sys.path` for mixed import styles.
  - Adds fixture `compat_bound_delivered_count` to temporarily count `deliveredEvents` as *number of bound layers*.

- **Metrics parity**
  - `src/python/metrics.py`: keep `delivered_events/total_slots/total_synapses` **and** `deliveredEvents/totalSlots/totalSynapses` in sync.

- **Slot API cleanup**
  - Remove `Neuron.slots()` method (name collision) and consistently use the `slots` dict.
  - Fix all call sites (`slot_engine.py`, `input_neuron.py`, `region.py`) to use `slots` dict.

- **Bus API alignment**
  - Canonical setters: `set_inhibition(...)`, `set_modulation(...)`.
  - Back-compat aliases retained: `set_inhibition_factor(...)`, `set_modulation_factor(...)`.
  - Neuron hooks use `self.fire_hooks`.

- **Input binding & delivered accounting**
  - `Region.bind_input`: if a target is an `InputLayer2D`, treat it as the port’s edge; wire it forward once. Avoid double-driving.
  - `Region.tick`/`tick_2d`: default `deliveredEvents = 1` per port event (V4). Optional compatibility via env var:
    - `GROWNET_COMPAT_DELIVERED_COUNT=bound` → report number of bound layers as `deliveredEvents`.
  - Tests updated to use the fixture where legacy counting is expected.

- **Docs & demos**
  - `docs/TESTING.md`: documents the env flag and fixture usage.
  - `src/python/demos/image_io_demo.py`: corrected imports & snake_case; fixed `add_input_layer_2d` typo.

## Semantics
- **Preserved:** *Ports are edges.* Each tick drives the port’s edge exactly once.
- **Compatibility:** Only the **reported** `deliveredEvents` can be toggled (for legacy expectations) via the fixture/env var. Delivery itself is unchanged.

## Public surface & compatibility notes
- `Neuron.slots()` removed (use `neuron.slots` dict). All in-repo call sites updated.
- `LateralBus`/`RegionBus`: canonical setters with compat aliases retained.
- `Region.bind_input`: convenience handling when an `InputLayer2D` is passed as a bound target.

## Test plan
- `pytest -q` → **all pass** with the updated fixture.
- Optional: `GROWNET_COMPAT_DELIVERED_COUNT=bound pytest -q` → also passes (compat mode).

## Risks & rollback
- Low risk. Behavior change limited to reported metrics if the compat flag is set.
- Rollback by removing the fixture usage in the affected test and/or unsetting the env flag.

## Follow-ups (separate PRs)
- Mirror small Python compatibility shims in **C++/Mojo** (only if needed by forthcoming tests).
- Incorporate temporal **Spatial Focus** demos/tests.
- Update high-level docs (Design Spec v4/Contract v4) once Morse-code temporal focus demo lands.

## Checklist
- [x] No removal of public methods without alternatives; `slots()` replaced with dict property and in-repo call sites updated.
- [x] V4 ports-as-edges semantics intact.
- [x] Tests green; docs updated.
