import math
from region import Region
from presets.topographic_wiring import TopographicConfig, connect_layers_topographic, get_topographic_weights, get_incoming_weight_sums


def test_unique_source_return_parity_and_normalization():
    region = Region("topo_test")
    src = region.add_input_layer_2d(8, 8, 1.0, 0.01)
    dst = region.add_output_layer_2d(8, 8, 0.0)

    cfg = TopographicConfig(kernel_h=3, kernel_w=3, stride_h=1, stride_w=1, padding="same", weight_mode="gaussian", sigma_center=1.5, normalize_incoming=True)
    unique_sources = connect_layers_topographic(region, src, dst, cfg)
    assert unique_sources == 64

    weights = get_topographic_weights(region, src, dst)
    sums = get_incoming_weight_sums(region, dst, weights)
    # All centers should have sums ~1.0 (within epsilon) when normalization is enabled
    for s_val in sums:
        if s_val > 0.0:
            assert abs(s_val - 1.0) < 1e-6


def test_gaussian_monotonic_with_distance():
    # Construct small geometry to test distances
    region = Region("topo_gauss")
    src = region.add_input_layer_2d(5, 5, 1.0, 0.01)
    dst = region.add_output_layer_2d(5, 5, 0.0)
    cfg = TopographicConfig(kernel_h=5, kernel_w=5, stride_h=1, stride_w=1, padding="valid", weight_mode="gaussian", sigma_center=2.0, normalize_incoming=False)
    connect_layers_topographic(region, src, dst, cfg)
    weights = get_topographic_weights(region, src, dst)
    # Pick the center pixel (2,2) in a 5x5, compare weight at distance 0 and 2
    center_index = 2 * 5 + 2
    weight_at_center = weights.get((2 * 5 + 2, center_index), 0.0)
    weight_one_step = weights.get((2 * 5 + 3, center_index), 0.0)
    weight_two_steps = weights.get((2 * 5 + 4, center_index), 0.0)
    assert weight_at_center > weight_one_step > weight_two_steps


def test_dog_non_negative_and_shape():
    region = Region("topo_dog")
    src = region.add_input_layer_2d(7, 7, 1.0, 0.01)
    dst = region.add_output_layer_2d(7, 7, 0.0)
    cfg = TopographicConfig(kernel_h=7, kernel_w=7, padding="valid", weight_mode="dog", sigma_center=1.5, sigma_surround=3.0, surround_ratio=0.5, normalize_incoming=False)
    connect_layers_topographic(region, src, dst, cfg)
    weights = get_topographic_weights(region, src, dst)
    # At zero distance, weight should be positive for DoG with surround_ratio < 1
    center_index = 3 * 7 + 3
    weight_at_zero = weights.get((3 * 7 + 3, center_index), 0.0)
    assert weight_at_zero > 0.0
    # All weights must be non-negative due to clamp
    assert all(w >= 0.0 for w in weights.values())


def test_determinism_two_runs_identical():
    region = Region("topo_determinism")
    src = region.add_input_layer_2d(6, 6, 1.0, 0.01)
    dst = region.add_output_layer_2d(6, 6, 0.0)
    cfg = TopographicConfig(kernel_h=3, kernel_w=3, padding="same", weight_mode="gaussian", sigma_center=1.7, normalize_incoming=True)
    connect_layers_topographic(region, src, dst, cfg)
    w1 = dict(get_topographic_weights(region, src, dst))
    # Re-invoke with same config; connect_layers_windowed is deterministic, weights should match
    connect_layers_topographic(region, src, dst, cfg)
    w2 = dict(get_topographic_weights(region, src, dst))
    assert w1 == w2
