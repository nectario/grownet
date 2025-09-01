from region import Region


def run_demo() -> None:
    h = w = 8
    region = Region("spatial_focus_demo")
    region.enable_spatial_metrics = True  # convenience for this demo

    l_in = region.add_input_layer_2d(h, w, gain=1.0, epsilon_fire=0.01)
    l_hid = region.add_layer(excitatory_count=12, inhibitory_count=0, modulatory_count=0)
    l_out = region.add_output_layer_2d(h, w, smoothing=0.10)

    # Enable spatial slotting in the hidden layer
    for n in region.get_layers()[l_hid].get_neurons():
        n.slot_cfg.spatial_enabled = True
        n.slot_cfg.row_bin_width_pct = 50.0
        n.slot_cfg.col_bin_width_pct = 50.0

    # Windowed deterministic wiring: 3x3 kernel, stride 2
    edges = region.connect_layers_windowed(l_in, l_hid, kernel_h=3, kernel_w=3, stride_h=2, stride_w=2, padding="valid")
    # Hidden → Output sparse feedforward (deterministic windowing is only on input side here)
    region.connect_layers(l_hid, l_out, probability=0.15, feedback=False)

    region.bind_input("pixels", [l_in])

    # Moving dot
    for step in range(10):
        frame = [[0.0 for _ in range(w)] for _ in range(h)]
        r = (step * 2) % h
        c = (step * 3) % w
        frame[r][c] = 1.0
        m = region.tick_image("pixels", frame)
        if (step + 1) % 2 == 0:
            print(f"[{step+1:02d}] delivered={m.delivered_events} "
                  f"active={m.active_pixels} centroid=({m.centroid_row:.2f},{m.centroid_col:.2f}) "
                  f"bbox={m.bbox} slots={m.total_slots} syn={m.total_synapses} edges={edges}")


if __name__ == "__main__":
    run_demo()

