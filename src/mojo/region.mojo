# src/mojo/region.mojo

from .region_metrics import RegionMetrics
# Import/forward-declare your types as needed:
# from .layer import Layer
# from .input_layer_2d import InputLayer2D
# from .output_layer_2d import OutputLayer2D
# from .region_bus import RegionBus
# from stdlib.list import List
# from stdlib.dict import Dict
# from stdlib.random import Random

struct PruneSummary:
    var pruned_synapses: Int
    var pruned_edges: Int

    fn __init__(mut self):
        self.pruned_synapses = 0
        self.pruned_edges = 0

struct Region:
    var input_edges: Dictionary[String, Int]
    var output_edges: Dictionary[String, Int]
    var layers: List[Layer]            # or whatever list/vector type you use
    var input_ports: Dictionary[String, List[Int]]
    var output_ports: Dictionary[String, List[Int]]
    var bus: RegionBus                  # or Optional if your code uses it

    fn __init__(mut self, name: String):
        self.name = name
        self.layers = List[any]()        # LayerRef
        self.input_ports = Dict[String, List[Int]]()
        self.output_ports = Dict[String, List[Int]]()
        self.bus = None                  # RegionBusRef


    fn tick(self, port: String, value: Float64) -> RegionMetrics:
        var metrics = RegionMetrics()

        # Prefer delivery to InputEdge if present
        let maybe_edge = self.input_edges.get(port)
        if maybe_edge is not None:
            let edge_index = maybe_edge
            self.layers[edge_index].forward(value)
            metrics.inc_delivered_events()
        else:
            # Fallback to original: fan directly into bound layers (if any)
            let maybe_bound = self.input_ports.get(port)
            if maybe_bound is not None:
                for entry_layer_index in maybe_bound:
                    self.layers[entry_layer_index].forward(value)
                    metrics.inc_delivered_events()

        # End-of-tick housekeeping: per-layer, then region bus decay
        for layer in self.layers:
            layer.end_tick()

        if self.bus is not None:
            self.bus.decay()

        # Aggregate structural metrics
        for layer in self.layers:
            for neuron in layer.get_neurons():
                metrics.add_slots(neuron.slots().size)        # or len(slots) equivalent
                metrics.add_synapses(neuron.get_outgoing().size)

        return metrics

    # In src/mojo/region.mojo (inside struct Region)

    fn tick_image(self, port: String, frame: List[List[Float64]]) -> RegionMetrics:
        var metrics = RegionMetrics()

        # Deliver the frame to all layers bound to this input port (shape-aware path)
        # We keep this identical to Python: call forward_image when available.
        if self.input_ports.contains(port):
            let bound_layers = self.input_ports[port]
            for layer_index in bound_layers:
                self.layers[layer_index].forward_image(frame)
                metrics.inc_delivered_events()

        # End-of-tick housekeeping
        for layer in self.layers:
            layer.end_tick()

        # Pulses are ephemeral; decay region bus once per tick
        if self.bus is not None:
            self.bus.decay()

        # Aggregate structural metrics
        for layer in self.layers:
            for neuron in layer.get_neurons():
                metrics.add_slots(neuron.slots().size)
                metrics.add_synapses(neuron.get_outgoing().size)

        return metrics


    # ---------------- construction ----------------
    fn add_layer(mut self,
                 excitatory_count: Int,
                 inhibitory_count: Int,
                 modulatory_count: Int) -> Int:
        # let layer = Layer(excitatory_count, inhibitory_count, modulatory_count)
        # self.layers.append(layer)
        # return self.layers.size - 1
        return 0

    fn add_input_layer_2d(mut self,
                          height: Int, width: Int,
                          gain: Float64, epsilon_fire: Float64) -> Int:
        # let layer = InputLayer2D(height, width, gain, epsilon_fire)
        # self.layers.append(layer)
        # return self.layers.size - 1
        return 0

    fn add_output_layer_2d(mut self,
                           height: Int, width: Int,
                           smoothing: Float64) -> Int:
        # let layer = OutputLayer2D(height, width, smoothing)
        # self.layers.append(layer)
        # return self.layers.size - 1
        return 0

    # ---------------- wiring ----------------
    fn connect_layers(mut self,
                      source_index: Int, dest_index: Int,
                      probability: Float64, feedback: Bool = False) -> Int:
        # Defensive bounds & clamping as in Python
        # Walk neurons in src/dst layers, probabilistic connect, return edge count
        return 0


    fn bind_input(self, port: String, layer_indices: List[Int]) -> None:
        # Record mapping for back-compat / diagnostics
        self.input_ports[port] = layer_indices

        # Ensure InputEdge(port) exists and wire it to bound layers with prob=1.0
        let input_edge_index = self.ensure_input_edge(port)
        for layer_index in layer_indices:
            self.connect_layers(input_edge_index, layer_index, 1.0, False)


    fn bind_output(self, port: String, layer_indices: List[Int]) -> None:
        self.output_ports[port] = layer_indices

        let output_edge_index = self.ensure_output_edge(port)
        for layer_index in layer_indices:
            self.connect_layers(layer_index, output_edge_index, 1.0, False)


    fn pulse_inhibition(self, factor: Float64) -> None:
        # Region-scope bus (if present)
        if self.bus is not None:
            self.bus.set_inhibition_factor(factor)

        # Mirror to each layer bus
        for layer in self.layers:
            if layer.bus is not None:
                layer.bus.set_inhibition_factor(factor)


    fn pulse_modulation(self, factor: Float64) -> None:
        if self.bus is not None:
            self.bus.set_modulation_factor(factor)

        for layer in self.layers:
            if layer.bus is not None:
                layer.bus.set_modulation_factor(factor)



    fn ensure_input_edge(self, port: String) -> Int:
        """Ensure an Input edge layer exists for this port; create lazily."""
        idx = self.input_edges.get(port)
        if idx is not None:
            return idx
        # Minimal scalar input edge: a 1-neuron layer that forwards to internal graph.
        edge_idx = self.add_layer(1, 0, 0)
        self.input_edges[port] = edge_idx
        return edge_idx


    fn ensure_output_edge(self, port: String) -> Int:
        """Ensure an Output edge layer exists for this port; create lazily."""
        idx = self.output_edges.get(port)
        if idx is not None:
            return idx
        # Minimal scalar output edge: a 1-neuron layer acting as a sink.
        edge_idx = self.add_layer(1, 0, 0)

        self.output_edges[port] = edge_idx

        return edge_idx


