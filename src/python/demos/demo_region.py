# demo_region.py
# Minimal scalar-drive demo for Region/Layer wiring

from region import Region


def main() -> None:
    region = Region("vision")

    # two small mixed-type layers
    l0 = region.add_layer(excitatory_count=8, inhibitory_count=2, modulatory_count=1)
    l1 = region.add_layer(excitatory_count=8, inhibitory_count=2, modulatory_count=1)

    # feedforward wiring from l0 -> l1
    region.connect_layers(l0, l1, probability=0.20, feedback=False)

    # bind a named input port to l0
    region.bind_input(port="pixels", layer_indices=[l0])

    # drive a simple scalar over 50 ticks
    for tick in range(50):
        # two plateaus to make %Δ vary
        value = 0.5 if tick < 25 else 0.9

        metrics = region.tick(port="pixels", value=value)

        if tick % 10 == 0:
            print(
                f"tick={tick:02d}  "
                f"delivered={metrics['delivered_events']:.0f}  "
                f"total_slots={metrics['total_slots']}  "
                f"total_synapses={metrics['total_synapses']}"
            )

    # optional maintenance: prune stale + weak connections
    summary = region.prune()
    print("pruned:", summary)


if __name__ == "__main__":
    main()
