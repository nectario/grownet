import math

from region import Region


def test_temporal_focus_creates_many_slots():
    r = Region("tfocus")
    L0 = r.add_layer(1, 0, 0)
    r.bind_input("in", [L0])

    # feed values from 1.0 to 2.0 (inclusive) in small steps
    steps = 50
    for loop_index in range(steps + 1):
        v = 1.0 + (i / steps)
        r.tick("in", v)

    # check total slots on first neuron
    n0 = r.layers[L0].get_neurons()[0]
    total_slots = len(n0.slots)
    assert total_slots >= 10, f"expected >=10 slots, got {total_slots}"

