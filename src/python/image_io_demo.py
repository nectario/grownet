import numpy as np
from region import Region

def main():
    h, w = 28, 28
    region = Region("image_io")
    l_in = region.add_input_layer_2d(h, w, gain=1.0, epsilon_fire=0.01)
    l_hidden = region.add_layer(excitatory_count=64, inhibitory_count=8, modulatory_count=4)
    l_out = region.add_output_layer_2d(h, w, smoothing=0.2)

    region.bind_input("pixels", [l_in])
    region.connect_layers(l_in, l_hidden, probability=0.05, feedback=False)
    region.connect_layers(l_hidden, l_out, probability=0.12, feedback=False)

    for step in range(20):
        frame = (np.random.rand(h, w) > 0.95).astype(float)
        metrics = region.tick_image("pixels", frame)
        if (step + 1) % 5 == 0:
            out = region.layers[l_out].get_frame()
            print(f"[{step+1}] delivered={metrics['delivered_events']:.0f} out_mean={out.mean():.3f} out_nonzero={(out>0.05).sum()}")

if __name__ == "__main__":
    main()
