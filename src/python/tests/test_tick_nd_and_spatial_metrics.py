import math

from region import Region


def test_tick_nd_basic():
    r = Region("nd-basic")
    # Ensure ND input edge exists; no attached target layers needed for delivery accounting
    r.bind_input_nd("nd", shape=[2, 3], gain=1.0, epsilon_fire=0.01, layer_indices=[])
    flat = [0.0] * 6

    m = r.tick_nd("nd", flat, [2, 3])
    assert m.get_delivered_events() == 1


def test_compute_spatial_metrics_public_wrapper():
    r = Region("spatial-metrics")
    # simple 2D image with a single active pixel at (0,1)
    img = [
        [0.0, 1.0, 0.0],
        [0.0, 0.0, 0.0],
    ]
    m = r.compute_spatial_metrics(img, prefer_output=False)
    assert m.active_pixels == 1
    assert math.isclose(m.centroid_row, 0.0, rel_tol=0.0, abs_tol=1e-12)
    assert math.isclose(m.centroid_col, 1.0, rel_tol=0.0, abs_tol=1e-12)
    assert m.bbox == (0, 0, 1, 1)
