from region import Region

fn generate_frame(height: Int64, width: Int64, step: Int64) -> Array[Array[Float64]]:
    var img = Array[Array[Float64]](height)
    for row_idx in range(height):
        var row = Array[Float64](width)
        for col_idx in range(width): row[Int(col_idx)] = 0.0
        img[Int(row_idx)] = row
    img[Int((step * 2) % height)][Int(step % width)] = 1.0
    return img

fn main():
    var height: Int64 = 28; var width: Int64 = 28
    var region = Region("image_io")

    var input_idx  = region.add_input_layer_2d(height, width, 1.0, 0.01)
    var hidden_idx = region.add_layer(64, 8, 4)
    var output_idx = region.add_output_layer_2d(height, width, 0.20)

    region.bind_input("pixels", [input_idx])
    region.connect_layers(input_idx,  hidden_idx, 0.05, False)
    region.connect_layers(hidden_idx, output_idx, 0.12, False)

    for step in range(20):
        var frame = generate_frame(height, width, step)
        var metrics = region.tick_image("pixels", frame)
        if ((step + 1) % 5) == 0:
            var delivered = metrics["delivered_events"]
            print("step=", step + 1, " delivered=", delivered)
