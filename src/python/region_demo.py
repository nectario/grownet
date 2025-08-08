# src/python/region_demo.py
import random
from region import Region

def main():
    region = Region("vision")
    l0 = region.add_layer(excitatory_count=40, inhibitory_count=8, modulatory_count=4)
    l1 = region.add_layer(excitatory_count=30, inhibitory_count=6, modulatory_count=3)

    # Bind input to the first layer
    region.bind_input("pixels", [l0])

    # Feedforward tract with sparse feedback
    region.connect_layers(l0, l1, probability=0.10, feedback=False)
    region.connect_layers(l1, l0, probability=0.01, feedback=True)

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
