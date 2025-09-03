from region import Region

fn generate_frame(height: Int, width: Int, step: Int) -> list[list[Float64]]:
    var img = []
    var r = 0
    while r < height:
        var row = []
        var c = 0
        while c < width:
            row.append(0.0)
            c = c + 1
        img.append(row)
        r = r + 1
    var rr = (step * 2) % height
    var cc = (step * 3) % width
    img[rr][cc] = 1.0
    return img

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
    var i = 0
    while i < neurons.len:
        neurons[i].slot_cfg.spatial_enabled = True
        neurons[i].slot_cfg.row_bin_width_pct = 50.0
        neurons[i].slot_cfg.col_bin_width_pct = 50.0
        i = i + 1

    # Deterministic windowed wiring: 3x3 kernel, stride 2
    var unique_source_count = region.connect_layers_windowed(input_layer_index, hidden_layer_index, 3, 3, 2, 2, "valid", False)
    # Hidden → Output sparse feedforward
    region.connect_layers(hidden_layer_index, output_layer_index, 0.15, False)

    region.bind_input("pixels", [input_layer_index])

    var step = 0
    while step < 10:
        var frame = generate_frame(height, width, step)
        var m = region.tick_image("pixels", frame)
        if ((step + 1) % 2) == 0:
            print("[", step + 1, "] delivered=", m.get_delivered_events(),
                  " active=", m.activePixels,
                  " centroid=(", m.centroidRow, ",", m.centroidCol, ")",
                  " bbox=(", m.bboxRowMin, ",", m.bboxRowMax, ",", m.bboxColMin, ",", m.bboxColMax, ")",
                  " unique_sources=", unique_source_count)
        step = step + 1

if __name__ == "__main__":
    main()
