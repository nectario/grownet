from presets.topographic_wiring import TopographicConfig, connect_layers_topographic, get_topographic_weights, get_incoming_weight_sums
from region import Region


def run_demo():
    region = Region("topographic_demo")
    src = region.add_input_layer_2d(16, 16, gain=1.0, epsilon_fire=0.01)
    dst = region.add_output_layer_2d(16, 16, smoothing=0.0)

    cfg = TopographicConfig(
        kernel_h=7, kernel_w=7,
        stride_h=1, stride_w=1,
        padding="same",
        weight_mode="gaussian",
        sigma_center=2.0,
        normalize_incoming=True,
    )

    unique_sources = connect_layers_topographic(region, src, dst, cfg)
    weights = get_topographic_weights(region, src, dst)
    sums = get_incoming_weight_sums(region, dst, weights)

    print(f"unique_sources={unique_sources}")
    # Sample a few centers: top-left, center, bottom-right
    centers = [(0, 0), (8, 8), (15, 15)]
    for (row_index, col_index) in centers:
        center_index = row_index * 16 + col_index
        sum_in = sums[center_index] if 0 <= center_index < len(sums) else 0.0
        # compute min/avg/max of incoming weights
        incoming = [w for (s_idx, c_idx), w in weights.items() if c_idx == center_index]
        if incoming:
            min_w = min(incoming)
            max_w = max(incoming)
            avg_w = sum(incoming) / len(incoming)
        else:
            min_w = max_w = avg_w = 0.0
        print(f"center=({row_index},{col_index})  sum={sum_in:.6f}  min={min_w:.6f}  avg={avg_w:.6f}  max={max_w:.6f}")


if __name__ == "__main__":
    run_demo()

