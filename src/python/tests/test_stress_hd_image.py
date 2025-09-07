import time
from region import Region


def test_hd_image_single_tick_timing():
    height, width = 1080, 1920
    region = Region("stress-hd")
    # Bind a 2D input edge; no downstream wiring necessary
    region.bind_input_2d("img", height, width, 1.0, 0.01, [])

    # Diagonal pattern frame
    frame = [[0.0 for _ in range(width)] for _ in range(height)]
    for r in range(height):
        frame[r][r % width] = 1.0

    # Warm-up
    region.tick_2d("img", frame)

    t0 = time.perf_counter()
    metrics = region.tick_2d("img", frame)
    dt_ms = (time.perf_counter() - t0) * 1000.0
    print(f"[PYTHON] HD 1920x1080 tick took ~{dt_ms:.1f} ms; delivered_events={metrics.delivered_events}")

    assert metrics.delivered_events == 1

