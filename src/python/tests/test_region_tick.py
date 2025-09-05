# src/python/test/test_region_tick.py
# Minimal unit tests (no pytest required). Run:
#   python -m test.run_smoke_tests
from region import Region

def test_single_tick_no_tracts():
    region = Region("t")
    input_layer_idx = region.add_layer(1, 0, 0)
    region.bind_input("x", [input_layer_idx])
    metrics = region.tick("x", 0.42)
    assert metrics.delivered_events == 1
    assert metrics.total_slots >= 1
    assert metrics.total_synapses >= 0

def test_connect_layers_full_mesh():
    region = Region("t")
    src = region.add_layer(2, 0, 0)
    dst = region.add_layer(3, 0, 0)
    edges = region.connect_layers(src, dst, 1.0, False)
    assert edges == 2 * 3

def test_image_input_event_count():
    region = Region("t")
    in_idx = region.add_input_layer_2d(2, 2, 1.0, 0.01)
    region.bind_input("pixels", [in_idx])
    frame = [[0.0, 1.0],[0.0, 0.0]]
    m = region.tick_image("pixels", frame)
    assert m.delivered_events == 1
