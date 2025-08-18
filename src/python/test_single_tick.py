# Tiny single-tick demo mirroring TestSingleTick.java for breakpoints.
from region import Region
from neuron import Neuron

def main():
    region = Region(name="dbg")
    l0 = region.add_layer(1, 0, 0)  # one excitatory neuron to drive
    l1 = region.add_layer(1, 0, 0)  # one neuron to observe fan-out

    region.bind_input("in", [l0])
    region.bind_output("out", [l1])
    edges = region.connect_layers(l0, l1, probability=1.0, feedback=False)
    print(f"Connected L{l0} -> L{l1} with {edges} edge(s)")

    # Hook for debugging (fires on each neuron emit)
    def hook(who: Neuron, value: float):
        print(f"FIRE id={who.get_id()} value={value:.6f}")

    for neuron in region.get_layers()[l0].get_neurons():
        neuron.register_fire_hook(hook)
    for neuron in region.get_layers()[l1].get_neurons():
        neuron.register_fire_hook(hook)

    # One scalar tick
    m = region.tick("in", 1.0)
    print(f"Metrics: delivered_events={m.get_delivered_events()}, "
          f"total_slots={m.get_total_slots()}, total_synapses={m.get_total_synapses()}")

if __name__ == "__main__":
    main()
