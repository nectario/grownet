# Session Worklog — 2025-09-01

This work session implemented Phase‑B Spatial Focus features and parity stubs, added a Python demo, completed C++ spatial metrics, and tightened a few edge cases. All changes are opt‑in and keep existing behavior/tests intact.

## Highlights
- Spatial slotting (2D) in Python with FIRST/ORIGIN anchoring and per‑axis bins.
- Deterministic 2D windowed wiring helper (`connect_layers_windowed`).
- Optional spatial metrics (activePixels, centroidRow/Col, bbox) for 2D ticks.
- New Python demo: spatial focus moving‑dot with metrics.
- C++: full spatial metrics in `Region::tickImage` + working `connectLayersWindowed` wiring.
- Mojo: parity stubs (anchors, 2D methods) to avoid API drift.
- Tightened behavior: deduped sink targets, accurate subscription counts, sane epsilon at origin.

## Python — Source changes
- `src/python/slot_config.py`
  - Added spatial knobs: `spatial_enabled`, `row_bin_width_pct`, `col_bin_width_pct` (defaults off).
- `src/python/slot_engine.py`
  - New: `slot_id_2d(anchor_rc, current_rc)` and `select_or_create_slot_2d(neuron, row, col)`.
  - Spatial epsilon set to `max(1.0, epsilon_scale)` to avoid exploding bins at ORIGIN.
- `src/python/neuron.py`
  - Added `focus_anchor_row`/`focus_anchor_col` and `on_input_2d(value, row, col)` (falls back to scalar when disabled).
- `src/python/layer.py`
  - Added `propagate_from_2d(source_index, value, height, width)` to drive spatial on_input.
- `src/python/tract.py`
  - Extended to carry 2D context; accepts `allowed_source_indices` and `sink_map` (now deduped).
- `src/python/region.py`
  - Added `connect_layers_windowed(...)` (deterministic wiring; returns unique subscription count).
  - Added `enable_spatial_metrics` flag and spatial metrics computation in `tick_2d`.
  - Internal `_compute_spatial_metrics(...)` helper; prefers downstream OutputLayer2D frame and falls back to input.
- `src/python/metrics.py`
  - Optional spatial fields and aliases: `active_pixels/activePixels`, `centroid_row/Row`, `centroid_col/Col`, `bbox` (+ split fields).

## Python — Demo & Tests
- Demo: `src/python/demos/spatial_focus_demo.py`
  - Moving dot across an 8×8 frame; prints delivered events, spatial metrics, slots/synapses.
  - Run: `PYTHONPATH=src/python python src/python/demos/spatial_focus_demo.py`
- Tests: `src/python/tests/test_spatial_focus.py`
  - Spatial slotting basic flow with windowed wiring.
  - Spatial metrics centroid/bbox under env flag.
  - Unique subscription count for windowed wiring.
  - Dedup behavior for explicit sink maps.
- Result: `pytest -q` → 14 passed (including new tests). With `GROWNET_ENABLE_SPATIAL_METRICS=1`: still passes.

## C++ — Parity & Features
- `src/cpp/Neuron.h`
  - Added `anchorRow/anchorCol` and `onInput2D(...)` defaulting to scalar path.
- `src/cpp/SlotEngine.h`
  - Added `slotId2D(...)` and `selectOrCreateSlot2D(...)` (minimal inline support).
- `src/cpp/Region.h`
  - Added spatial metrics fields to `RegionMetrics` and `bool enableSpatialMetrics { false };`.
  - Added `connectLayersWindowed(...)` signature.
- `src/cpp/Region.cpp`
  - Implemented `connectLayersWindowed(...)` deterministically (valid/same padding); returns unique source subscriptions.
  - Completed spatial metrics in `tickImage(...)` (env `GROWNET_ENABLE_SPATIAL_METRICS=1` or flag).

## Mojo — Parity Stubs
- `src/mojo/neuron.mojo`: spatial anchors + `on_input_2d` defaulting to scalar.
- `src/mojo/slot_engine.mojo`: `slot_id_2d(...)` added.
- `src/mojo/region.mojo`: `connect_layers_windowed(...)` stub for compile parity.

## Docs
- `docs/SPATIAL_FOCUS.md` — new; how to enable spatial slotting, use windowed wiring, and read spatial metrics.
- `docs/TESTING.md` — spatial metrics env‑flag section.
- `docs/DEMO_RUN.md` — added spatial focus demo run snippet.

## Flags & Opt‑in Behavior
- Spatial slotting is disabled by default; enable per neuron: `n.slot_cfg.spatial_enabled = True`.
- Spatial metrics are disabled by default; enable with `GROWNET_ENABLE_SPATIAL_METRICS=1` or per‑region flag (`Region.enable_spatial_metrics` in Python; `enableSpatialMetrics` in C++).
- Delivered events semantics unchanged; legacy bound‑count shim remains via `GROWNET_COMPAT_DELIVERED_COUNT=bound`.

## Compatibility & Risk
- No breaking changes to existing APIs; additions are backward‑compatible.
- Python and C++ spatial metrics are guarded by flags; overhead is avoided when off.
- Deterministic windowed wiring avoids RNG and deduplicates targets to prevent double delivery.

## Validation
- Python: `pytest -q` — 14 tests passed.
- Demo: Python moving‑dot runs and prints centroid/bbox when metrics enabled.
- C++: spatial metrics logic mirrors Python and remains opt‑in; windowed wiring compiles and is deterministic.

