from region import Region

fn generate_frame(height: Int, width: Int, step: Int) -> list[list[Float64]]:
    var image = []
    var row_index = 0
    while row_index < height:
        var row = []
        var col_index = 0
        while col_index < width:
            row.append(0.0)
            col_index = col_index + 1
        image.append(row)
        row_index = row_index + 1
    var bright_row = (step * 2) % height
    var bright_col = (step * 3) % width
    image[bright_row][bright_col] = 1.0
    return image

fn main():
    var height: Int = 8
    var width: Int = 8
    var region = Region("spatial_focus_demo")
    region.enable_spatial_metrics = True

    var input_layer_index = region.add_input_layer_2d(height, width, 1.0, 0.01)
    var hidden_layer_index = region.add_layer(12, 0, 0)
    var output_layer_index = region.add_output_layer_2d(height, width, 0.10)

    # Enable spatial slotting on hidden neurons (coarse 2x2 bins => 50% per axis)
    var neurons = region.get_layers()[hidden_layer_index].get_neurons()
    var neuron_index = 0
    while neuron_index < neurons.len:
        neurons[neuron_index].slot_cfg.spatial_enabled = True
        neurons[neuron_index].slot_cfg.row_bin_width_pct = 50.0
        neurons[neuron_index].slot_cfg.col_bin_width_pct = 50.0
        neuron_index = neuron_index + 1

    # Deterministic windowed wiring: 3x3 kernel, stride 2
    var unique_source_count = region.connect_layers_windowed(input_layer_index, hidden_layer_index, 3, 3, 2, 2, "valid", False)
    # Hidden → Output sparse feedforward
    region.connect_layers(hidden_layer_index, output_layer_index, 0.15, False)

    region.bind_input("pixels", [input_layer_index])

    var step = 0
    while step < 10:
        var frame = generate_frame(height, width, step)
        var metrics = region.tick_image("pixels", frame)
        if ((step + 1) % 2) == 0:
            print("[", step + 1, "] delivered=", metrics.delivered_events,
                  " active=", metrics.active_pixels,
                  " centroid=(", metrics.centroid_row, ",", metrics.centroid_col, ")",
                  " bbox=", metrics.bbox,
                  " unique_sources=", unique_source_count)
        step = step + 1

if __name__ == "__main__":
    main()
