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
