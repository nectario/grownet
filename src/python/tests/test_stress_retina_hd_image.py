from region import Region
from presets.topographic_wiring import TopographicConfig, connect_layers_topographic
import time


def test_hd_image_retina_single_tick_timing():
    height, width = 1080, 1920
    region = Region("stress-retina-hd")
    in_idx = region.add_input_layer_2d(height, width, 1.0, 0.01)
    out_idx = region.add_output_layer_2d(height, width, 0.0)

    cfg = TopographicConfig(kernel_h=7, kernel_w=7, stride_h=1, stride_w=1, padding="same",
                            weight_mode="gaussian", normalize_incoming=True)
    unique = connect_layers_topographic(region, in_idx, out_idx, cfg)
    assert unique > 0

    region.bind_input_2d("img", height, width, 1.0, 0.01, [in_idx])

    # Diagonal frame
    frame = [[0.0 for _ in range(width)] for _ in range(height)]
    for r in range(height):
        frame[r][r % width] = 1.0

    # Warm-up
    region.tick_2d("img", frame)

    t0 = time.perf_counter()
    metrics = region.tick_2d("img", frame)
    dt_ms = (time.perf_counter() - t0) * 1000.0
    print(f"[PYTHON] Retina HD 1920x1080 tick took ~{dt_ms:.1f} ms; delivered_events={metrics.delivered_events}")
    assert metrics.delivered_events == 1

