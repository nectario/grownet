from region import Region
from topographic_wiring import TopographicConfig, connect_layers_topographic

fn test_stress_retina_hd_image_tick():
    var region = Region("stress-retina-hd")
    var height = 1080
    var width = 1920
    var in_idx = region.add_input_layer_2d(height, width, 1.0, 0.01)
    var out_idx = region.add_output_layer_2d(height, width, 0.0)
    var cfg = TopographicConfig()
    cfg.kernel_h = 7; cfg.kernel_w = 7
    cfg.stride_h = 1; cfg.stride_w = 1
    cfg.padding = "same"
    cfg.weight_mode = "gaussian"
    cfg.normalize_incoming = True
    var unique = connect_layers_topographic(region, in_idx, out_idx, cfg)
    # Bind 2D input to the in_idx edge and run two ticks
    region.bind_input_2d("img", height, width, 1.0, 0.01, [in_idx])
    var frame = []
    var r = 0
    while r < height:
        var row = []
        var c = 0
        while c < width:
            row.append(0.0)
            c = c + 1
        row[r % width] = 1.0
        frame.append(row)
        r = r + 1
    _ = region.tick_image("img", frame)
    var metrics = region.tick_image("img", frame)
    print("[MOJO] Retina HD 1920x1080 tick executed; delivered_events=", metrics.delivered_events)

fn main():
    test_stress_retina_hd_image_tick()
    print("[MOJO] stress_retina_hd_image passed.")

