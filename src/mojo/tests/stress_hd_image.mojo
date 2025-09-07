from region import Region

fn test_stress_hd_image_tick():
    var region = Region("stress-hd")
    var height = 1080
    var width = 1920
    region.bind_input_2d("img", height, width, 1.0, 0.01, [])
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

    # Warm-up
    _ = region.tick_image("img", frame)
    # Timing API not standardized in this environment; simply execute the second tick
    var metrics = region.tick_image("img", frame)
    print("[MOJO] HD 1920x1080 tick executed; delivered_events=", metrics.delivered_events)

fn main():
    test_stress_hd_image_tick()
    print("[MOJO] stress_hd_image passed.")

