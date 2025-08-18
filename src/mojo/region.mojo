from region_bus import RegionBus
from layer import Layer, Spike
from input_layer_2d import InputLayer2D
from output_layer_2d import OutputLayer2D
from tract import Tract
from region_metrics import RegionMetrics

struct PruneSummary:
    var pruned_synapses: Int = 0
    var pruned_edges: Int = 0

struct Region:
    var name: String
    var layers: list[Layer]
    var tracts: list[Tract]
    var bus: RegionBus
    var input_ports: dict[String, list[Int]]
    var output_ports: dict[String, list[Int]]

    fn init(mut self, name: String) -> None:
        self.name = name
        self.layers = []
        self.tracts = []
        self.bus = RegionBus()
        self.input_ports = dict[String, list[Int]]()
        self.output_ports = dict[String, list[Int]]()

    fn add_layer(mut self, excitatory_count: Int, inhibitory_count: Int, modulatory_count: Int) -> Int:
        let idx = Int(self.layers.size())
        self.layers.append(Layer(excitatory_count, inhibitory_count, modulatory_count))
        return idx

    fn connect_layers(mut self, source_index: Int, dest_index: Int, probability: Float64, feedback: Bool = False) -> Tract:
        # For now we only record the connection. The demo uses fan-out probability at creation time.
        let t = Tract(source_index, dest_index, feedback)
        self.tracts.append(t)
        return t

    fn bind_input(mut self, port: String, layer_indices: list[Int]) -> None:
        self.input_ports[port] = layer_indices

    fn bind_output(mut self, port: String, layer_indices: list[Int]) -> None:
        self.output_ports[port] = layer_indices

    fn tick(mut self, port: String, value: Float64) -> RegionMetrics:
        var m = RegionMetrics()
        if self.input_ports.contains(port):
            for li in self.input_ports[port]:
                let spikes = self.layers[li].forward(value)
                m.delivered_events += 1
                # route through tracts originating at li
                for t in self.tracts:
                    if t.source_index == li:
                        for s in spikes:
                            # Currently assume 1:1 mapping of neuron index across layers
                            # and numeric dest index.
                            let dest_idx = t.dest_index
                            # Only OutputLayer2D has propagate_from in this minimal port; for other layers,
                            # you can route into .forward(value) similarly.
                            # Here we do nothing, since generic Layer doesn't have propagate_from.
                            pass
        # End-of-tick
        for L in self.layers:
            L.end_tick()
        return m

    fn get_name(self) -> String:
        return self.name

    fn get_layers(self) -> List[Any]:
        return self.layers
