from region import Region

fn main() -> None:
    var height: Int = 8
    var width: Int = 8

    var region = Region("two-d-tick-demo")

    var input_index = region.add_input_layer_2d(height, width, 1.0, 0.01)
    var output_index = region.add_output_layer_2d(height, width, 0.0)

    var unique_sources = region.connect_layers_windowed(
        input_index, output_index,
        3, 3,
        1, 1,
        "same",
        False)
    print("unique_sources=", unique_sources)

    # Bind input edge
    var attach: list[Int] = []
    attach.append(input_index)
    region.bind_input_2d("pixels", height, width, 1.0, 0.01, attach)

    # Build zero frame
    var frame = [] as list[list[Float64]]
    var r_index = 0
    while r_index < height:
        var row_list = [] as list[Float64]
        var c_index = 0
        while c_index < width:
            row_list.append(0.0)
            c_index = c_index + 1
        frame.append(row_list)
        r_index = r_index + 1

    # Tick #1 with a bright pixel
    frame[3][4] = 1.0
    var metrics1 = region.tick_2d("pixels", frame)
    print("tick#1 delivered=", metrics1.delivered_events,
          " slots=", metrics1.total_slots,
          " synapses=", metrics1.total_synapses)

    # Tick #2, move bright pixel
    frame[3][4] = 0.0
    frame[5][6] = 1.0
    var metrics2 = region.tick_2d("pixels", frame)
    print("tick#2 delivered=", metrics2.delivered_events,
          " slots=", metrics2.total_slots,
          " synapses=", metrics2.total_synapses)

