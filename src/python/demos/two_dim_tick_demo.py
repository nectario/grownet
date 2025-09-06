from region import Region


def run_demo() -> None:
    height, width = 8, 8
    region = Region("two-d-tick-demo")

    input_index = region.add_input_layer_2d(height, width, gain=1.0, epsilon_fire=0.01)
    output_index = region.add_output_layer_2d(height, width, smoothing=0.0)

    unique_sources = region.connect_layers_windowed(
        input_index, output_index,
        kernel_h=3, kernel_w=3,
        stride_h=1, stride_w=1,
        padding="same",
    )
    print(f"unique_sources={unique_sources}")

    # Enable spatial metrics to compute active/centroid/bbox
    region.enable_spatial_metrics = True
    region.bind_input_2d("pixels", height, width, gain=1.0, epsilon_fire=0.01, attach_layers=[input_index])

    # Frame 1: single bright pixel near the center
    frame = [[0.0 for _ in range(width)] for _ in range(height)]
    frame[3][4] = 1.0
    metrics1 = region.tick_2d("pixels", frame)
    print(
        f"tick#1 delivered={metrics1.delivered_events} slots={metrics1.total_slots} synapses={metrics1.total_synapses} "
        f"active={metrics1.active_pixels} centroid=({metrics1.centroid_row:.3f},{metrics1.centroid_col:.3f}) bbox={metrics1.bbox}"
    )

    # Frame 2: move the bright pixel to exercise a different mapping
    frame[3][4] = 0.0
    frame[5][6] = 1.0
    metrics2 = region.tick_2d("pixels", frame)
    print(
        f"tick#2 delivered={metrics2.delivered_events} slots={metrics2.total_slots} synapses={metrics2.total_synapses} "
        f"active={metrics2.active_pixels} centroid=({metrics2.centroid_row:.3f},{metrics2.centroid_col:.3f}) bbox={metrics2.bbox}"
    )


if __name__ == "__main__":
    run_demo()
