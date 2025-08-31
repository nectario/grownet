# src/python/region_demo.py
import random
from region import Region

def main():
    region = Region("vision")
    layer_in = region.add_layer(excitatory_count=40, inhibitory_count=8, modulatory_count=4)
    layer_out = region.add_layer(excitatory_count=30, inhibitory_count=6, modulatory_count=3)

    # Bind input to the first layer
    region.bind_input("pixels", [layer_in])

    # Feedforward tract with sparse feedback
    region.connect_layers(layer_in, layer_out, probability=0.10, feedback=False)
    region.connect_layers(layer_out, layer_in, probability=0.01, feedback=True)

    for step in range(2_000):
        value = random.random()
        metrics = region.tick("pixels", value)
        if (step + 1) % 200 == 0:
            print(f"[step {step+1}] delivered={metrics['delivered_events']:.0f} "
                  f"slots={metrics['total_slots']:.0f} syn={metrics['total_synapses']:.0f}")

    print("Pruning...")
    print(region.prune())

if __name__ == "__main__":
    main()
