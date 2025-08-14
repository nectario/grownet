# region.mojo — add layers, bind inputs, tick, prune summary

from bus   import LateralBus
from layer import Layer

struct RegionMetrics:
    var delivered_events: Int64
    var total_slots:      Int64
    var total_synapses:   Int64

struct PruneSummary:
    var pruned_synapses: Int64
    var pruned_edges:    Int64

struct Region:
    var name:   String
    var layers: List[Layer]
    var bus:    LateralBus
    var input_ports:  Dict[String, List[Int64]]  # name → layer indices

    fn init(name: String) -> None:
        self.name  = name
        self.layers = []
        self.bus    = LateralBus()
        self.input_ports = {}

    fn add_layer(self, excitatory_count: Int64, inhibitory_count: Int64, modulatory_count: Int64) -> Int64:
        let l = Layer(excitatory_count, inhibitory_count, modulatory_count)
        self.layers.append(l)
        return Int64(self.layers.len) - 1

    fn bind_input(self, port: String, layer_indices: List[Int64]) -> None:
        self.input_ports[port] = layer_indices

    fn tick(self, port: String, value: F64) -> RegionMetrics:
        # A: drive entry layers
        let found = self.input_ports.get(port)
        if found is List[Int64]:
            for idx in found:
                self.layers[Int64(idx)].forward(value)

        # B: decay buses (simple demo)
        for l in self.layers:
            l.decay()
        self.bus.decay()

        # C: light metrics
        var total_slots: Int64 = 0
        for l in self.layers:
            for n in l.neurons:
                total_slots = total_slots + Int64(n.slots.len)

        return RegionMetrics(delivered_events=0, total_slots=total_slots, total_synapses=0)

    fn prune(self) -> PruneSummary:
        # placeholder: wiring-level pruning lives in Tract/Graph; keep API
        return PruneSummary(pruned_synapses=0, pruned_edges=0)
