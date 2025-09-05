from region import Region


def test_spatial_slotting_first_anchor_and_bins():
    region = Region("spatial")
    l_in = region.add_input_layer_2d(4, 4, 1.0, 0.01)
    l_hid = region.add_layer(excitatory_count=8, inhibitory_count=0, modulatory_count=0)

    # Enable spatial slotting in hidden neurons (coarse 2x2 bins => 50% per axis)
    layer = region.get_layers()[l_hid]
    for n in layer.get_neurons():
        n.slot_cfg.spatial_enabled = True
        n.slot_cfg.row_bin_width_pct = 50.0
        n.slot_cfg.col_bin_width_pct = 50.0

    # Deterministic windowing: 2x2 kernel, stride 2 (valid)
    region.connect_layers_windowed(l_in, l_hid, kernel_h=2, kernel_w=2, stride_h=2, stride_w=2, padding="valid")
    region.bind_input("img", [l_in])

    # Tick a frame with a bright pixel at (1,1)
    f1 = [[0, 0, 0, 0],
          [0, 1, 0, 0],
          [0, 0, 0, 0],
          [0, 0, 0, 0]]
    region.tick_2d("img", f1)

    # Shift to (1,2) — expect different (rowBin, colBin) tuple for at least some neuron
    f2 = [[0, 0, 0, 0],
          [0, 0, 1, 0],
          [0, 0, 0, 0],
          [0, 0, 0, 0]]
    m = region.tick_2d("img", f2)

    # Structural evidence of slotting occurred
    assert m.total_slots >= 1


def test_spatial_metrics_centroid_and_bbox(monkeypatch):
    import os
    monkeypatch.setenv("GROWNET_ENABLE_SPATIAL_METRICS", "1")

    region = Region("spatial_metrics")
    l_in = region.add_input_layer_2d(3, 3, 1.0, 0.01)
    l_out = region.add_output_layer_2d(3, 3, smoothing=0.0)

    # Use simple full fanout wiring; metrics will fall back to input frame if no output activity
    region.connect_layers(l_in, l_out, probability=1.0, feedback=False)
    region.bind_input("img", [l_in, l_out])

    frame = [
        [0, 0.5, 0],
        [0, 1.0, 0],
        [0, 0,   0],
    ]
    m = region.tick_2d("img", frame)

    assert m.active_pixels >= 1

    # Weighted centroid should lie near the (1,1) neighborhood
    assert 0.0 <= m.centroid_row <= 2.0
    assert 0.0 <= m.centroid_col <= 2.0
    r0, r1, c0, c1 = m.bbox
    assert r0 <= r1 and c0 <= c1


def test_connect_layers_windowed_returns_unique_subscriptions():
    region = Region("wires_count")
    l_in = region.add_input_layer_2d(4, 4, 1.0, 0.01)
    l_out = region.add_output_layer_2d(4, 4, smoothing=0.0)

    # Single valid 4x4 window → every pixel participates exactly once.
    wires = region.connect_layers_windowed(
        l_in, l_out, kernel_h=4, kernel_w=4, stride_h=1, stride_w=1, padding="valid"
    )
    assert wires == 16


def test_sink_map_dedup_for_output_layer():
    from tract import Tract

    class DummyNeuron:
        def __init__(self): self.calls = 0
        def on_input(self, v): self.calls += 1; return False
        def on_output(self, v): pass

    class DummyDst:
        def __init__(self, n=10): self.neurons = [DummyNeuron() for _ in range(n)]
        def get_neurons(self): return self.neurons

    class DummySrc:
        def get_neurons(self): return []

    dst = DummyDst()

    # Duplicate same center three times for a single source index
    t = Tract(DummySrc(), dst, None, False, None,
              allowed_source_indices=None,
              sink_map={5: [3, 3, 3]})
    t.on_source_fired(5, 1.0)
    assert dst.get_neurons()[3].calls == 1
