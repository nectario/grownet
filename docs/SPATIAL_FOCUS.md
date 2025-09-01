# Spatial Focus (Phase B)

This document describes the Python reference implementation of Spatial Focus and the parity stubs added for other languages.

## What it is

- Spatial slotting lets neurons form coarse 2D “location bins” relative to a spatial anchor `(row, col)`, analogous to Temporal Focus’ FIRST anchor.
- Anchoring policy: `anchor_mode` supports `FIRST` (set on first strong event) and `ORIGIN` (treat `(0,0)` as the anchor). Defaults remain unchanged unless enabled.

## How to enable (Python)

Enable per receiving neuron (typically a hidden layer) by setting flags on its `slot_cfg`:

```python
for n in region.layers[hidden_idx].get_neurons():
    n.slot_cfg.spatial_enabled = True
    n.slot_cfg.row_bin_width_pct = 50.0
    n.slot_cfg.col_bin_width_pct = 50.0
```

When spatial is enabled, `Neuron.on_input_2d(value, row, col)` is used during propagation. The `SlotEngine` selects or creates a slot keyed by `(rowBin, colBin)`, with capacity clamped by `slot_limit`.

## Windowed wiring helper

Use `Region.connect_layers_windowed(...)` to wire an `InputLayer2D` to a destination layer deterministically using sliding windows:

```python
edges = region.connect_layers_windowed(
    src_index=l_in,
    dest_index=l_hid,
    kernel_h=2, kernel_w=2,
    stride_h=2, stride_w=2,
    padding="valid",
)
```

- If destination is `OutputLayer2D`: each window forwards all its source pixels to the output neuron at the window’s center.
- Otherwise: allowed source pixels forward to `Layer.propagate_from_2d(...)`, which computes `(row,col)` and calls `on_input_2d` per neuron.
- Returns a deterministic count of “wires” (subscription hooks) created.

## Spatial metrics (optional)

Set `GROWNET_ENABLE_SPATIAL_METRICS=1` (or set `Region.enable_spatial_metrics = True`) to populate:

- `active_pixels`/`activePixels`
- `centroid_row/centroidRow`, `centroid_col/centroidCol`
- `bbox` tuple `(row_min, row_max, col_min, col_max)`

Metrics prefer the furthest‑downstream `OutputLayer2D` frame; if no non‑zero output is present, they fall back to the input frame.

### Quick demo

```bash
# from repo root
PYTHONPATH=src/python python src/python/demos/spatial_focus_demo.py
```

## Parity stubs (C++/Java/Mojo)

- Add spatial anchors to `Neuron` (`anchorRow/anchorCol`) and an `onInput2D(...)` method that defaults to scalar `onInput`.
- Add `slotId2D`/`selectOrCreateSlot2D` stubs to `SlotEngine`.
- Add `connectLayersWindowed(...)` signature to `Region` (minimal deterministic implementation is preferred; a no‑op stub is acceptable initially).
- Add optional spatial metrics fields to `RegionMetrics` (computation can be deferred).

Defaults remain unchanged: Spatial Focus is off unless enabled on the receiving layer’s neurons. Spatial metrics are off unless explicitly toggled.
