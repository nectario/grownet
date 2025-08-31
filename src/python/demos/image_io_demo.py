from region import Region
from output_layer_2d import OutputLayer2D

def run_demo():
    h = w = 8
    region = Region("py_image_io")
    l_in = region.add_input_layer_2d(h, w, 1.0, 0.01)
    l_hid = region.add_layer(16, 4, 2)
    l_out = region.add_output_layer_2d(h, w, 0.20)
    region.bind_input("pixels", [l_in])
    region.connect_layers(l_in, l_hid, 0.05, False)
    region.connect_layers(l_hid, l_out, 0.10, False)

    import random
    rnd = random.Random(42)

    for step in range(5):
        # generate sparse frame
        frame = [[1.0 if rnd.random() > 0.95 else 0.0 for _ in range(w)] for _ in range(h)]
        m = region.tick_image("pixels", frame)

        if (step + 1) % 5 == 0:
            out = region.get_layers()[l_out]
            if isinstance(out, OutputLayer2D):
                img = out.get_frame()
                s = sum(sum(row) for row in img)
                print(f"[{step+1:02d}] delivered={m.delivered_events} out_mean={s / (h * w):.3f}")
