# Testing Notes

This repo uses a unified Region/Layer/Neuron API across languages. Python tests live under `src/python/tests/` and assume the Python sources are importable without packaging; the test `conftest.py` adjusts `sys.path` accordingly.

## Delivered events accounting

GrowNet V4 treats input ports as edges: binding an input creates/uses a single edge layer per port which is driven once per tick. Under this model, per‑tick `deliveredEvents` defaults to `1` per port event.

Some legacy tests count “number of bound layers” instead. To enable that accounting for specific tests, set the environment flag:

```
GROWNET_COMPAT_DELIVERED_COUNT=bound
```

The Python tests include a fixture you can use to scope this behavior to a single test:

```python
@pytest.mark.usefixtures("compat_bound_delivered_count")
def test_something():
    ...
```

This does not change tick delivery — the edge is still driven once — it only adjusts the reported `deliveredEvents` for compatibility.

## Spatial metrics (optional)

Set the environment flag below to compute simple spatial metrics during `tick_2d`:

```
GROWNET_ENABLE_SPATIAL_METRICS=1
```

When enabled, `Region.tick_2d` populates these optional fields on `RegionMetrics`:
- `active_pixels`/`activePixels`: count of pixels with value > 0.0
- `centroid_row`/`centroidRow`, `centroid_col`/`centroidCol`: weighted centroid (weights = pixel values)
- `bbox`: `(row_min, row_max, col_min, col_max)` for active pixels (or `(0, -1, 0, -1)` if empty)

It prefers the frame from the most downstream `OutputLayer2D`; if no non‑zero output exists, it falls back to the input frame driven this tick.
