# region.mojo
from bus import LateralBus
from layer import Layer

struct Region:
    var name: String
    var layers: Array[Layer]
    var bus: LateralBus

    fn init(self, name: String) -> None:
        self.name = name
        self.layers = Array[Layer]()
        self.bus = LateralBus()

    fn add_layer(self, excitatory_count: Int64, inhibitory_count: Int64, modulatory_count: Int64) -> Int64:
        var layer = Layer(excitatory_count, inhibitory_count, modulatory_count)
        self.layers.push(layer)
        return Int64(self.layers.len - 1)

    # For now: deliver 'value' to every entry layer, then decay the region bus.
    fn tick(self, port: String, value: F64) -> None:
        for layer in self.layers:
            layer.forward(value)
        self.bus.decay()
    # inside struct Region { ... }

    fn prune(
        self,
        synapse_stale_window: Int64 = 10_000,
        synapse_min_strength: F64 = 0.05) -> (pruned_synapses: Int64, pruned_edges: Int64):
        var removed: Int64 = 0
        for l in self.layers:
            for n in l.neurons:
                # assumes each neuron has prune_synapses(current_step, stale_window, min_strength) -> Int64
                removed += n.prune_synapses(self.bus.current_step, synapse_stale_window, synapse_min_strength)
        return (removed, 0)

