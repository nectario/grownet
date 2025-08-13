# region_demo.mojo
# Minimal end-to-end run showing the two-phase tick at Region level.

from region import Region
from math_utils import pseudo_random_pair

fn main():
    var region = Region(name="vision")
    var l0 = region.add_layer(40, 8, 4)
    var l1 = region.add_layer(30, 6, 3)

    region.bind_input("pixels", [l0])
    _ = region.connect_layers(l0, l1, 0.10, False)
    _ = region.connect_layers(l1, l0, 0.01, True)

    for step in range(2000):
        var value = pseudo_random_pair(Int64(step), 17)
        var m = region.tick("pixels", value)
        if (step + 1) % 200 == 0:
            print("[step {step+1}] delivered={m.delivered_events} slots={m.total_slots} syn={m.total_synapses}")

    var p = region.prune()
    print("Prune summary: syn={p.pruned_synapses} edges={p.pruned_edges}")

if __name__ == "__main__":
    main()

