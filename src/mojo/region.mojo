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
# region.mojo — Mojo Region implementation (Python-parity: fn/struct/typed)

from metrics import RegionMetrics
from layer import Layer
from input_layer_2d import InputLayer2D
from input_layer_nd import InputLayerND
from output_layer_2d import OutputLayer2D
from region_bus import RegionBus

struct MeshRule:
    var src: Int
    var dst: Int
    var prob: Float64
    var feedback: Bool

struct Region:
    var name: String
    var layers: list[any]
    var input_ports: dict[String, list[Int]]
    var output_ports: dict[String, list[Int]]
    var input_edges: dict[String, Int]
    var output_edges: dict[String, Int]
    var bus: RegionBus
    var mesh_rules: list[MeshRule]
    var enable_spatial_metrics: Bool
    var rng_state: UInt64

    fn init(mut self, name: String) -> None:
        self.name = name
        self.layers = []
        self.input_ports = dict[String, list[Int]]()
        self.output_ports = dict[String, list[Int]]()
        self.input_edges = dict[String, Int]()
        self.output_edges = dict[String, Int]()
        self.bus = RegionBus()
        self.mesh_rules = []
        self.enable_spatial_metrics = False
        self.rng_state = 0x9E3779B97F4A7C15

    fn get_name(self) -> String:
        return self.name

    fn get_layers(self) -> list[any]:
        return self.layers

    fn get_bus(self) -> RegionBus:
        return self.bus

    # ---------------- construction ----------------
    fn add_layer(mut self, excitatory_count: Int, inhibitory_count: Int, modulatory_count: Int) -> Int:
        var L = Layer(excitatory_count, inhibitory_count, modulatory_count)
        self.layers.append(L)
        return self.layers.len - 1

    fn add_input_layer_2d(mut self, height: Int, width: Int, gain: Float64, epsilon_fire: Float64) -> Int:
        var L = InputLayer2D(height, width, gain, epsilon_fire)
        self.layers.append(L)
        return self.layers.len - 1

    fn add_input_layer_nd(mut self, shape: list[Int], gain: Float64, epsilon_fire: Float64) -> Int:
        var L = InputLayerND(shape, gain, epsilon_fire)
        self.layers.append(L)
        return self.layers.len - 1

    fn add_output_layer_2d(mut self, height: Int, width: Int, smoothing: Float64) -> Int:
        var L = OutputLayer2D(height, width, smoothing)
        self.layers.append(L)
        return self.layers.len - 1

    # ---------------- RNG ----------------
    fn rand_f64(mut self) -> Float64:
        var x = self.rng_state
        x = x ^ (x >> 12)
        x = x ^ (x << 25)
        x = x ^ (x >> 27)
        self.rng_state = x
        var v: UInt64 = x * 0x2545F4914F6CDD1D
        return Float64(v & 0xFFFFFFFFFFFF) / Float64(0x1000000000000)

    # ---------------- wiring ----------------
    fn connect_layers(mut self, source_index: Int, dest_index: Int, probability: Float64, feedback: Bool = False) -> Int:
        var edges: Int = 0
        var src = self.layers[source_index]
        var dst = self.layers[dest_index]
        var src_neurons = src.get_neurons()
        var dst_neurons = dst.get_neurons()
        var i = 0
        while i < src_neurons.len:
            var j = 0
            while j < dst_neurons.len:
                if self.rand_f64() <= probability:
                    # Store target index; propagation is a later concern
                    src_neurons[i].connect(j, feedback)
                    edges = edges + 1
                j = j + 1
            i = i + 1
        self.mesh_rules.append(MeshRule(source_index, dest_index, probability, feedback))
        return edges

    fn connect_layers_windowed(mut self,
                               src_index: Int,
                               dest_index: Int,
                               kernel_h: Int,
                               kernel_w: Int,
                               stride_h: Int = 1,
                               stride_w: Int = 1,
                               padding: String = "valid",
                               feedback: Bool = False) -> Int:
        # Deterministic unique source subscriptions like Python
        var src_any = self.layers[src_index]
        var dst_any = self.layers[dest_index]
        var src2d = src_any  # expect InputLayer2D
        var H = src2d.height
        var W = src2d.width
        var kh = kernel_h
        var kw = kernel_w
        var sh = if stride_h > 0 then stride_h else 1
        var sw = if stride_w > 0 then stride_w else 1
        var same = (padding == "same" or padding == "SAME")

        # Window origins
        var origins: list[tuple[Int, Int]] = []
        if same:
            var pr = (kh - 1) / 2
            var pc = (kw - 1) / 2
            var r = -pr
            while r + kh <= H + pr + pr:
                var c = -pc
                while c + kw <= W + pc + pc:
                    origins.append((r, c))
                    c = c + sw
                r = r + sh
        else:
            var r = 0
            while r + kh <= H:
                var c = 0
                while c + kw <= W:
                    origins.append((r, c))
                    c = c + sw
                r = r + sh

        # Unique set of participating source pixel indices
        var allowed = dict[Int, Bool]()
        var idx = 0
        while idx < origins.len:
            var r0 = origins[idx][0]; var c0 = origins[idx][1]
            var rr0 = if r0 > 0 then r0 else 0
            var cc0 = if c0 > 0 then c0 else 0
            var rr1 = if (r0 + kh) < H then (r0 + kh) else H
            var cc1 = if (c0 + kw) < W then (c0 + kw) else W
            if rr0 < rr1 and cc0 < cc1:
                var rr = rr0
                while rr < rr1:
                    var cc = cc0
                    while cc < cc1:
                        var src_idx = rr * W + cc
                        allowed[src_idx] = True
                        cc = cc + 1
                    rr = rr + 1
            idx = idx + 1
        return Int(allowed.size())

    # ---------------- edge helpers ----------------
    fn ensure_input_edge(mut self, port: String) -> Int:
        if self.input_edges.contains(port):
            return self.input_edges[port]
        # Minimal scalar input edge: a 1-neuron layer that forwards downstream
        var edge = self.add_layer(1, 0, 0)
        self.input_edges[port] = edge
        return edge

    fn ensure_output_edge(mut self, port: String) -> Int:
        if self.output_edges.contains(port):
            return self.output_edges[port]
        var edge = self.add_layer(1, 0, 0)
        self.output_edges[port] = edge
        return edge

    fn bind_input(mut self, port: String, layer_indices: list[Int]) -> None:
        self.input_ports[port] = layer_indices
        var edge = self.ensure_input_edge(port)
        var i = 0
        while i < layer_indices.len:
            self.connect_layers(edge, layer_indices[i], 1.0, False)
            i = i + 1

    fn bind_input_2d(mut self, port: String, height: Int, width: Int, gain: Float64, epsilon_fire: Float64, layer_indices: list[Int]) -> None:
        var need_new = True
        if self.input_edges.contains(port):
            var idx = self.input_edges[port]
            var maybe = self.layers[idx]
            # crude type check: InputLayer2D has 'height' field
            if maybe.height == height and maybe.width == width:
                need_new = False
        var idx2: Int
        if not self.input_edges.contains(port) or need_new:
            idx2 = self.add_input_layer_2d(height, width, gain, epsilon_fire)
            self.input_edges[port] = idx2
        else:
            idx2 = self.input_edges[port]
        self.input_ports[port] = layer_indices
        var i = 0
        while i < layer_indices.len:
            self.connect_layers(idx2, layer_indices[i], 1.0, False)
            i = i + 1

    fn bind_output(mut self, port: String, layer_indices: list[Int]) -> None:
        self.output_ports[port] = layer_indices
        var edge = self.ensure_output_edge(port)
        var i = 0
        while i < layer_indices.len:
            self.connect_layers(layer_indices[i], edge, 1.0, False)
            i = i + 1

    fn bind_input_nd(mut self, port: String, shape: list[Int], gain: Float64, epsilon_fire: Float64, layer_indices: list[Int]) -> None:
        var need_new = True
        if self.input_edges.contains(port):
            var idx = self.input_edges[port]
            var maybe = self.layers[idx]
            if maybe.has_shape(shape):
                need_new = False
        var idx2: Int
        if not self.input_edges.contains(port) or need_new:
            idx2 = self.add_input_layer_nd(shape, gain, epsilon_fire)
            self.input_edges[port] = idx2
        else:
            idx2 = self.input_edges[port]
        self.input_ports[port] = layer_indices
        var i = 0
        while i < layer_indices.len:
            self.connect_layers(idx2, layer_indices[i], 1.0, False)
            i = i + 1

    # ---------------- pulses ----------------
    fn pulse_inhibition(mut self, factor: Float64) -> None:
        # region bus + per-layer buses
        self.bus.set_inhibition_factor(factor)
        var i = 0
        while i < self.layers.len:
            var L = self.layers[i]
            L.get_bus().set_inhibition_factor(factor)
            i = i + 1

    fn pulse_modulation(mut self, factor: Float64) -> None:
        self.bus.set_modulation_factor(factor)
        var i = 0
        while i < self.layers.len:
            var L = self.layers[i]
            L.get_bus().set_modulation_factor(factor)
            i = i + 1

    # ---------------- ticks ----------------
    fn tick(mut self, port: String, value: Float64) -> RegionMetrics:
        var metrics = RegionMetrics()
        if not self.input_edges.contains(port):
            raise Exception("No InputEdge for port '" + port + "'. Call bind_input(...) first.")
        var edge_idx = self.input_edges[port]
        self.layers[edge_idx].forward(value)

        if self.input_ports.contains(port):
            var targets = self.input_ports[port]
            var i = 0
            while i < targets.len:
                var li = targets[i]
                if li != edge_idx:
                    self.layers[li].forward(value)
                i = i + 1
        metrics.inc_delivered_events(1)

        # End-of-tick housekeeping
        var li2 = 0
        while li2 < self.layers.len:
            self.layers[li2].end_tick()
            li2 = li2 + 1

        # Aggregate structural metrics
        var li3 = 0
        while li3 < self.layers.len:
            var N = self.layers[li3].get_neurons()
            var ni = 0
            while ni < N.len:
                metrics.add_slots(Int64(N[ni].slots.size()))
                metrics.add_synapses(Int64(N[ni].outgoing.size()))
                ni = ni + 1
            li3 = li3 + 1
        return metrics

    fn tick_2d(mut self, port: String, frame: list[list[Float64]]) -> RegionMetrics:
        var metrics = RegionMetrics()
        if not self.input_edges.contains(port):
            raise Exception("No InputEdge for port '" + port + "'. Call bind_input_2d(...) first.")
        var edge_idx = self.input_edges[port]
        self.layers[edge_idx].forward_image(frame)
        metrics.inc_delivered_events(1)

        var i = 0
        while i < self.layers.len:
            self.layers[i].end_tick()
            i = i + 1

        var li3 = 0
        while li3 < self.layers.len:
            var N = self.layers[li3].get_neurons()
            var ni = 0
            while ni < N.len:
                metrics.add_slots(Int64(N[ni].slots.size()))
                metrics.add_synapses(Int64(N[ni].outgoing.size()))
                ni = ni + 1
            li3 = li3 + 1
        return metrics

    fn tick_image(mut self, port: String, frame: list[list[Float64]]) -> RegionMetrics:
        return self.tick_2d(port, frame)

    fn tick_nd(mut self, port: String, flat: list[Float64], shape: list[Int]) -> RegionMetrics:
        var metrics = RegionMetrics()
        if not self.input_edges.contains(port):
            raise Exception("No InputEdge for port '" + port + "'. Call bind_input_nd(...) first.")
        var edge_idx = self.input_edges[port]
        self.layers[edge_idx].forward_nd(flat, shape)
        metrics.inc_delivered_events(1)

        var i = 0
        while i < self.layers.len:
            self.layers[i].end_tick()
            i = i + 1

        var li3 = 0
        while li3 < self.layers.len:
            var N = self.layers[li3].get_neurons()
            var ni = 0
            while ni < N.len:
                metrics.add_slots(Int64(N[ni].slots.size()))
                metrics.add_synapses(Int64(N[ni].outgoing.size()))
                ni = ni + 1
            li3 = li3 + 1
        return metrics
