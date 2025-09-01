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
    var h: Int64 = 28; var w: Int64 = 28
    var region = Region("image_io")

    var in_idx  = region.add_input_layer_2d(h, w, 1.0, 0.01)
    var hid_idx = region.add_layer(64, 8, 4)
    var out_idx = region.add_output_layer_2d(h, w, 0.20)

    region.bind_input("pixels", [in_idx])
    region.connect_layers(in_idx,  hid_idx, 0.05, False)
    region.connect_layers(hid_idx, out_idx, 0.12, False)

    for step in range(20):
        var frame = generate_frame(h, w, step)
        var m = region.tick_image("pixels", frame)
        if ((step + 1) % 5) == 0:
            var delivered = m["delivered_events"]
            print("step=", step + 1, " delivered=", delivered)
