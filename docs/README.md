# GrowNet (Python Reference)

This folder contains the Python reference implementation of GrowNet with
slot-based neurons, inhibitory and modulatory dynamics, and region/layer wiring.

## Quick start

```bash
python -m src.python.demo_region
```

## Tests

```bash
pytest -q
```

## Mojo Demos

Run the lightweight Mojo demos to exercise the cross‑language API and (optionally) spatial metrics.

- Image I/O demo (prints delivered events and spatial stats):

  ```bash
  mojo run src/mojo/image_io_demo.mojo
  ```

- Spatial focus demo (windowed wiring + spatial slotting in the hidden layer):

  ```bash
  mojo run src/mojo/spatial_focus_demo.mojo
  ```

Notes
- Both demos enable `region.enable_spatial_metrics = True` and print:
  - `activePixels` (non‑zero pixels),
  - `centroidRow/centroidCol` (weighted by pixel values),
  - `bboxRowMin/Max` and `bboxColMin/Max`.
- The spatial demo also prints the number of unique source subscriptions created by windowed wiring.
- To turn off spatial metrics, set `region.enable_spatial_metrics = False` in the demo.

---

## More Docs

- Coding Style (MUST READ): `docs/CODING_STYLE_MUST_READ.md`
- Read Order (start here): `docs/READ_ORDER.md`
- Changelog (latest session): `docs/changelog/SESSION_WORKLOG_2025-09-03.md`
- Changelog (PR‑13 Auto‑Growth Parity Finish): `docs/changelog/CHANGELOG_2025-09-04_PR13.md`

Note
- Region spillover wiring default is deterministic: saturated → new uses probability p = 1.0 (policies may override explicitly).

---

## 2D Tick Demos

Run small 2D demos that wire an 8×8 input to an 8×8 output with a 3×3 SAME window and tick two frames with a single bright pixel.

- Python
  - `PYTHONPATH=src/python python src/python/demos/two_dim_tick_demo.py`
  - Prints: `unique_sources`, then per‑tick `delivered_events`, `total_slots`, `total_synapses`.

- Mojo
  - `mojo run src/mojo/tests/two_dim_tick_demo.mojo`
  - Prints: `unique_sources`, then per‑tick metrics.

- C++ (CMake)
  - Build targets in `src/cpp` (see `src/cpp/CMakeLists.txt`), then run:
    - `two_dim_tick_demo`
  - Prints: `unique_sources`, then per‑tick metrics.

- Java (IDE)
  - `src/java/ai/nektron/grownet/demo/TwoDimTickDemo.java`
  - Set breakpoints in `Region.connectLayersWindowed`, `Region.tick2D`, `InputLayer2D.forwardImage`, `Tract.onSourceFiredIndex`, `OutputLayer2D.propagateFrom`.
