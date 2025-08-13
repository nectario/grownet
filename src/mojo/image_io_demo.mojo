from region import Region

fn generate_frame(h: Int64, w: Int64, step: Int64) -> Array[Array[Float64]]:
    var img = Array[Array[Float64]](h)
    for y in range(h):
        var row = Array[Float64](w)
        for x in range(w): row[Int(x)] = 0.0
        img[Int(y)] = row
    img[Int((step * 2) % h)][Int(step % w)] = 1.0
    return img

fn main():
    let h: Int64 = 28; let w: Int64 = 28
    var region = Region("image_io")

    let in_idx  = region.add_input_layer_2d(h, w, 1.0, 0.01)
    let hid_idx = region.add_layer(64, 8, 4)
    let out_idx = region.add_output_layer_2d(h, w, 0.20)

    region.bind_input("pixels", [in_idx])
    region.connect_layers(in_idx,  hid_idx, 0.05, False)
    region.connect_layers(hid_idx, out_idx, 0.12, False)

    for step in range(20):
        let frame = generate_frame(h, w, step)
        let m = region.tick_image("pixels", frame)
        if ((step + 1) % 5) == 0:
            let delivered = m["delivered_events"]
            print("step=", step + 1, " delivered=", delivered)
