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


    # Drive a scalar into the edge bound to `port` and collect metrics.
    fn tick(self, port: String, value: Float64) -> RegionMetrics:
        var metrics = RegionMetrics()

        # Prefer delivery to InputEdge if present
        var maybe_edge = self.input_edges.get(port)
        if maybe_edge is not None:
            var edge_index = maybe_edge
            self.layers[edge_index].forward(value)
            metrics.inc_delivered_events()
        else:

            # Fallback to original: fan directly into bound layers (if any)
            var maybe_bound = self.input_ports.get(port)
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

    

// Drive a 2D frame into an InputLayer2D edge bound to `port`.
fn tick_2d(mut self, port: String, frame: List[List[Float64]]) -> RegionMetrics:
    var metrics = RegionMetrics()

    var maybe_edge = self.input_edges.get(port)
    if maybe_edge is None:
        raise Exception("No InputEdge for port '" + port + "'. Call bind_input_2d(...) first.")
    var edge_index = maybe_edge

    # Expect the edge layer to implement forward_image(...)
    self.layers[edge_index].forward_image(frame)
    metrics.inc_delivered_events(1)

    # End-of-tick housekeeping
    for layer_ref in self.layers:
        layer_ref.end_tick()

    if self.bus is not None:
        self.bus.decay()

    # Aggregate structural metrics
    for layer_ref in self.layers:
        for neuron in layer_ref.get_neurons():
            metrics.add_slots(neuron.slots().size)
            metrics.add_synapses(neuron.get_outgoing().size)
    return metrics
fn tick_image(mut self, port: String, frame: List[List[Float64]]) -> RegionMetrics:
        return self.tick_2d(port, frame)

    # Windowed deterministic wiring helper (parity stub)
    fn connect_layers_windowed(self,
        src_index: Int, dest_index: Int,
        kernel_h: Int, kernel_w: Int,
        stride_h: Int = 1, stride_w: Int = 1,
        padding: String = "valid",
        feedback: Bool = False) -> Int:
        # TODO: implement deterministic windowed wiring (Phase B parity)
        return 0
