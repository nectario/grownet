# image_io_demo.mojo
# Minimal end-to-end demo using Region with Input/Output 2D layers.
# Assumes Region exposes:
#   - add_input_layer_2d(h, w, gain, epsilon_fire)
#   - add_layer(excitatory_count, inhibitory_count, modulatory_count)
#   - add_output_layer_2d(h, w, smoothing)
#   - bind_input(port: String, layer_indices: Array[Int64])
#   - connect_layers(src, dst, probability, feedback)
#   - tick_image(port: String, image: Array[Array[Float64]]) -> Dict[String, Float64]
#
# And OutputLayer2D has end_tick() called inside Region.tick(), so frames are ready after a tick.
#
from region import Region

fn zeros(height: Int64, width: Int64) -> Array[Array[Float64]]:
    var img = Array[Array[Float64]](height)
    for y in range(height):
        var row = Array[Float64](width)
        for x in range(width):
            row[x] = 0.0
        img[y] = row
    return img

fn generate_frame(height: Int64, width: Int64, step: Int64) -> Array[Array[Float64]]:
    var img = zeros(height, width)
    # simple moving dot so we don't rely on RNG
    var y = (step * 2) % height
    var x = step % width
    img[Int(y)][Int(x)] = 1.0
    return img

fn main():
    var h: Int64 = 28
    var w: Int64 = 28
    var region = Region("image_io")

    let in_idx = region.add_input_layer_2d(h, w, 1.0, 0.01)
    let hidden_idx = region.add_layer(64, 8, 4)
    let out_idx = region.add_output_layer_2d(h, w, 0.2)

    region.bind_input("pixels", [in_idx])
    region.connect_layers(in_idx, hidden_idx, 0.05, False)
    region.connect_layers(hidden_idx, out_idx, 0.12, False)

    for step in range(20):
        let frame = generate_frame(h, w, step)
        let metrics = region.tick_image("pixels", frame)
        if ((step + 1) % 5) == 0:
            # We print the metrics we know are returned by tick_image
            # (delivered_events, total_slots, total_synapses). Adjust keys if different.
            print("step=", step + 1,
                  " delivered=", metrics["delivered_events"],
                  " slots=", metrics["total_slots"],
                  " synapses=", metrics["total_synapses"])
