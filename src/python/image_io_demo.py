
from .. import Region, OutputLayer2D

def run_demo():
    h = w = 8
    region = Region("py_image_io")
    l_in = region.addInputLayer2D(h, w, 1.0, 0.01)
    l_hid = region.addLayer(16, 4, 2)
    l_out = region.addOutputLayer2D(h, w, 0.20)
    region.bindInput("pixels", [l_in])
    region.connectLayers(l_in, l_hid, 0.05, False)
    region.connectLayers(l_hid, l_out, 0.10, False)

    import random
    rnd = random.Random(42)

    for step in range(5):
        # generate sparse frame
        frame = [[1.0 if rnd.random() > 0.95 else 0.0 for _ in range(w)] for _ in range(h)]
        m = region.tickImage("pixels", frame)

        if (step + 1) % 5 == 0:
            out = region.getLayers()[l_out]
            if isinstance(out, OutputLayer2D):
                img = out.getFrame()
                s = sum(sum(row) for row in img)
                print(f"[{step+1:02d}] delivered={m.deliveredEvents} out_mean={s/(h*w):.3f}")
