from __future__ import annotations

import numpy as np
from region import Region


def main() -> None:
    height, width = 28, 28

    region = Region("image_io")

    # Construct a simple three‑stage pipeline: IN(2D) -> hidden -> OUT(2D)
    input_index  = region.add_input_layer_2d(height, width, gain=1.0, epsilon_fire=0.01)
    hidden_index = region.add_layer(excitatory_count=64, inhibitory_count=8, modulatory_count=4)
    output_index = region.add_output_layer_2d(height, width, smoothing=0.2)

    # Bind a named input port to the input layer
    region.bind_input(port="pixels", layer_indices=[input_index])

    # Random wiring (feedforward only for this demo)
    region.connect_layers(input_index, hidden_index, probability=0.05, feedback=False)
    region.connect_layers(hidden_index, output_index, probability=0.12, feedback=False)

    for step in range(20):
        # Random sparse “sparkles” frame in [0,1]
        frame = (np.random.rand(height, width) > 0.95).astype(float)

        # Drive the region with the image and advance one tick
        metrics = region.tick_image("pixels", frame)

        if (step + 1) % 5 == 0:
            out = region.layers[output_index].get_frame()
            print(
                f"[step {step+1:02d}] delivered={metrics['delivered_events']:.0f} "
                f"out_mean={out.mean():.3f} out_nonzero={(out > 0.05).sum()}"
            )


if __name__ == "__main__":
    main()
