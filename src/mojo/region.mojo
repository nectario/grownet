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
from growth_policy import GrowthPolicy
from growth_engine import maybe_grow

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
    var output_layer_indices: list[Int]
    var growth_policy: GrowthPolicy
    var growth_policy_enabled: Bool
    var last_layer_growth_step: Int

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
        self.output_layer_indices = []
        self.growth_policy = GrowthPolicy()
        self.growth_policy_enabled = False
        self.last_layer_growth_step = -1

    fn get_name(self) -> String:
        return self.name

    fn get_layers(self) -> list[any]:
        return self.layers

    fn get_bus(self) -> RegionBus:
        return self.bus

    fn set_growth_policy(mut self, policy: GrowthPolicy) -> None:
        self.growth_policy = policy
        self.growth_policy_enabled = True

    fn get_growth_policy(self) -> GrowthPolicy:
        return self.growth_policy

    # ---------------- construction ----------------
    fn add_layer(mut self, excitatory_count: Int, inhibitory_count: Int, modulatory_count: Int) -> Int:
        var new_layer = Layer(excitatory_count, inhibitory_count, modulatory_count)
        # best-effort region backref for autowiring
        if new_layer.set_region is not None:
            new_layer.set_region(self)
        self.layers.append(new_layer)
        return self.layers.len - 1

    fn add_input_layer_2d(mut self, height: Int, width: Int, gain: Float64, epsilon_fire: Float64) -> Int:
        var new_input_layer_2d = InputLayer2D(height, width, gain, epsilon_fire)
        self.layers.append(new_input_layer_2d)
        return self.layers.len - 1

    fn add_input_layer_nd(mut self, shape: list[Int], gain: Float64, epsilon_fire: Float64) -> Int:
        var new_input_layer_nd = InputLayerND(shape, gain, epsilon_fire)
        self.layers.append(new_input_layer_nd)
        return self.layers.len - 1

    fn add_output_layer_2d(mut self, height: Int, width: Int, smoothing: Float64) -> Int:
        var new_output_layer = OutputLayer2D(height, width, smoothing)
        self.layers.append(new_output_layer)
        var idx = self.layers.len - 1
        self.output_layer_indices.append(idx)
        return idx

    # ---------------- RNG ----------------
    fn rand_f64(mut self) -> Float64:
        var random_state = self.rng_state
        random_state = random_state ^ (random_state >> 12)
        random_state = random_state ^ (random_state << 25)
        random_state = random_state ^ (random_state >> 27)
        self.rng_state = random_state
        var mixed_bits: UInt64 = random_state * 0x2545F4914F6CDD1D
        return Float64(mixed_bits & 0xFFFFFFFFFFFF) / Float64(0x1000000000000)

    # ---------------- wiring ----------------
    fn connect_layers(mut self, source_index: Int, dest_index: Int, probability: Float64, feedback: Bool = False) -> Int:
        var edge_count: Int = 0
        var source_layer = self.layers[source_index]
        var dest_layer = self.layers[dest_index]
        var source_neurons = source_layer.get_neurons()
        var dest_neurons = dest_layer.get_neurons()
        var source_counter = 0
        while source_counter < source_neurons.len:
            var dest_counter = 0
            while dest_counter < dest_neurons.len:
                if self.rand_f64() <= probability:
                    # Store target index; propagation is a later concern
                    source_neurons[source_counter].connect(dest_counter, feedback)
                    edge_count = edge_count + 1
                dest_counter = dest_counter + 1
            source_counter = source_counter + 1
        self.mesh_rules.append(MeshRule(source_index, dest_index, probability, feedback))
        return edge_count

    fn connect_layers_windowed(mut self,
                               src_index: Int,
                               dest_index: Int,
                               kernel_h: Int,
                               kernel_w: Int,
                               stride_h: Int = 1,
                               stride_w: Int = 1,
                               padding: String = "valid",
                               feedback: Bool = False) -> Int:
        # Deterministic unique source subscriptions; center rule if dest is OutputLayer2D
        var source_layer = self.layers[src_index]
        var dest_layer = self.layers[dest_index]
        var source_height = source_layer.height
        var source_width = source_layer.width
        var kernel_height = kernel_h
        var kernel_width = kernel_w
        var stride_height = if stride_h > 0 then stride_h else 1
        var stride_width = if stride_w > 0 then stride_w else 1
        var same = (padding == "same" or padding == "SAME")

        # Window origins
        var origins: list[tuple[Int, Int]] = []
        if same:
            var pad_rows = (kernel_height - 1) / 2
            var pad_cols = (kernel_width - 1) / 2
            var r0 = -pad_rows
            while r0 + kernel_height <= source_height + pad_rows + pad_rows:
                var c0 = -pad_cols
                while c0 + kernel_width <= source_width + pad_cols + pad_cols:
                    origins.append((r0, c0))
                    c0 = c0 + stride_width
                r0 = r0 + stride_height
        else:
            var r0v = 0
            while r0v + kernel_height <= source_height:
                var c0v = 0
                while c0v + kernel_width <= source_width:
                    origins.append((r0v, c0v))
                    c0v = c0v + stride_width
                r0v = r0v + stride_height

        # Unique participating sources
        var allowed_sources = dict[Int, Bool]()
        # Optional dedupe for created edges
        var made: dict[String, Bool] = {}

        # Check if dest is OutputLayer2D by duck-typing height/width and get_neurons
        var dst_has_frame = (dest_layer.height is not None) and (dest_layer.width is not None) and (dest_layer.get_frame is not None)
        if dst_has_frame:
            var dest_height = dest_layer.height
            var dest_width = dest_layer.width
            var oi = 0
            while oi < origins.len:
                var orow = origins[oi][0]
                var ocol = origins[oi][1]
                var rstart = if orow > 0 then orow else 0
                var cstart = if ocol > 0 then ocol else 0
                var rend = if (orow + kernel_height) < source_height then (orow + kernel_height) else source_height
                var cend = if (ocol + kernel_width) < source_width then (ocol + kernel_width) else source_width
                if rstart < rend and cstart < cend:
                    var center_r = orow + (kernel_height / 2)
                    if center_r < 0: center_r = 0
                    if center_r > (source_height - 1): center_r = source_height - 1
                    var center_c = ocol + (kernel_width / 2)
                    if center_c < 0: center_c = 0
                    if center_c > (source_width - 1): center_c = source_width - 1
                    # Clamp to destination bounds
                    if center_r > (dest_height - 1): center_r = dest_height - 1
                    if center_c > (dest_width - 1): center_c = dest_width - 1
                    var center_idx = center_r * dest_width + center_c
                    var rr = rstart
                    while rr < rend:
                        var cc = cstart
                        while cc < cend:
                            var sidx = rr * source_width + cc
                            allowed_sources[sidx] = True
                            var key = String(sidx) + ":" + String(center_idx)
                            if not made.contains(key):
                                # connect sidx -> center_idx once
                                self.layers[src_index].get_neurons()[sidx].connect(center_idx, feedback)
                                made[key] = True
                            cc = cc + 1
                        rr = rr + 1
                oi = oi + 1
        else:
            # Generic destination: connect each participating source to all dest neurons once
            var oi2 = 0
            while oi2 < origins.len:
                var or2 = origins[oi2][0]
                var oc2 = origins[oi2][1]
                var rstart2 = if or2 > 0 then or2 else 0
                var cstart2 = if oc2 > 0 then oc2 else 0
                var rend2 = if (or2 + kernel_height) < source_height then (or2 + kernel_height) else source_height
                var cend2 = if (oc2 + kernel_width) < source_width then (oc2 + kernel_width) else source_width
                if rstart2 < rend2 and cstart2 < cend2:
                    var rr2 = rstart2
                    while rr2 < rend2:
                        var cc2 = cstart2
                        while cc2 < cend2:
                            var sidx2 = rr2 * source_width + cc2
                            if not allowed_sources.contains(sidx2):
                                allowed_sources[sidx2] = True
                                var dj = 0
                                var dest_neurons = dest_layer.get_neurons()
                                while dj < dest_neurons.len:
                                    self.layers[src_index].get_neurons()[sidx2].connect(dj, feedback)
                                    dj = dj + 1
                            cc2 = cc2 + 1
                        rr2 = rr2 + 1
                oi2 = oi2 + 1
        return Int(allowed_sources.size())

    # Request a spillover layer and wire deterministically (snake_case; Python-Mojo parity)
    fn request_layer_growth(mut self, layerRef: any, connection_probability: Float64 = 1.0) -> Int:
        var li = -1
        var i = 0
        while i < self.layers.len:
            if self.layers[i] == layerRef:
                li = i
                break
            i = i + 1
        if li < 0:
            return -1
        var new_index = self.add_layer(4, 0, 0)
        _ = self.connect_layers(li, new_index, connection_probability, False)
        return new_index

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
        var layer_index_endtick = 0
        while layer_index_endtick < self.layers.len:
            self.layers[layer_index_endtick].end_tick()
            layer_index_endtick = layer_index_endtick + 1

        # Aggregate structural metrics
        var layer_index_aggregate = 0
        while layer_index_aggregate < self.layers.len:
            var neuron_list = self.layers[layer_index_aggregate].get_neurons()
            var neuron_index = 0
            while neuron_index < neuron_list.len:
                metrics.add_slots(Int64(neuron_list[neuron_index].slots.size()))
                metrics.add_synapses(Int64(neuron_list[neuron_index].outgoing.size()))
                neuron_index = neuron_index + 1
            layer_index_aggregate = layer_index_aggregate + 1
        # Consider automatic region growth (after end_tick aggregation)
        if self.growth_policy_enabled:
            _ = maybe_grow(self, self.growth_policy)
        return metrics

    fn tick_2d(mut self, port: String, frame: list[list[Float64]]) -> RegionMetrics:
        var metrics = RegionMetrics()
        if not self.input_edges.contains(port):
            raise Exception("No InputEdge for port '" + port + "'. Call bind_input_2d(...) first.")
        var edge_idx = self.input_edges[port]
        self.layers[edge_idx].forward_image(frame)
        metrics.inc_delivered_events(1)

        var layer_index_tick = 0
        while layer_index_tick < self.layers.len:
            self.layers[layer_index_tick].end_tick()
            layer_index_tick = layer_index_tick + 1

        var layer_index_aggregate2 = 0
        while layer_index_aggregate2 < self.layers.len:
            var neuron_list2 = self.layers[layer_index_aggregate2].get_neurons()
            var neuron_index2 = 0
            while neuron_index2 < neuron_list2.len:
                metrics.add_slots(Int64(neuron_list2[neuron_index2].slots.size()))
                metrics.add_synapses(Int64(neuron_list2[neuron_index2].outgoing.size()))
                neuron_index2 = neuron_index2 + 1
            layer_index_aggregate2 = layer_index_aggregate2 + 1

        # Optional spatial metrics: prefer last OutputLayer2D frame, fall back to input if all-zero
        if self.enable_spatial_metrics:
            var chosen = frame
            if self.output_layer_indices.len > 0:
                var out_idx = self.output_layer_indices[self.output_layer_indices.len - 1]
                var img = self.layers[out_idx].get_frame()
                # Check if all zero
                var all_zero = True
                var rr = 0
                while rr < Int(img.size()):
                    var cc = 0
                    while cc < Int(img[rr].size()):
                        if img[rr][cc] != 0.0:
                            all_zero = False
                            break
                        cc = cc + 1
                    if not all_zero: break
                    rr = rr + 1
                if not all_zero:
                    chosen = img

            var frame_height = Int(chosen.size())
            var frame_width = 0
            if frame_height > 0:
                frame_width = Int(chosen[0].size())
            var total = 0.0
            var sumR = 0.0
            var sumC = 0.0
            var rmin = 1000000000
            var rmax = -1
            var cmin = 1000000000
            var cmax = -1
            var active: Int64 = 0
            var r = 0
            while r < frame_height:
                var c = 0
                while c < frame_width:
                    var v = chosen[r][c]
                    if v > 0.0:
                        active = active + 1
                        total = total + v
                        sumR = sumR + (Float64(r) * v)
                        sumC = sumC + (Float64(c) * v)
                        if r < rmin: rmin = r
                        if r > rmax: rmax = r
                        if c < cmin: cmin = c
                        if c > cmax: cmax = c
                    c = c + 1
                r = r + 1
            metrics.activePixels = active
            if total > 0.0:
                metrics.centroidRow = sumR / total
                metrics.centroidCol = sumC / total
            else:
                metrics.centroidRow = 0.0
                metrics.centroidCol = 0.0
            if rmax >= rmin and cmax >= cmin:
                metrics.bboxRowMin = rmin
                metrics.bboxRowMax = rmax
                metrics.bboxColMin = cmin
                metrics.bboxColMax = cmax
            else:
                metrics.bboxRowMin = 0
                metrics.bboxRowMax = -1
                metrics.bboxColMin = 0
                metrics.bboxColMax = -1
        # Consider automatic region growth (after end_tick aggregation)
        if self.growth_policy_enabled:
            _ = maybe_grow(self, self.growth_policy)
        return metrics

    # -------- autowiring for grown neurons (by layer ref) --------
    fn autowire_new_neuron_by_ref(mut self, layer_ref: any, new_idx: Int) -> None:
        # find layer index
        var li = -1
        var i = 0
        while i < self.layers.len:
            if self.layers[i] == layer_ref:
                li = i
                break
            i = i + 1
        if li < 0: return

        # Outbound mesh: this layer -> dst
        var r = 0
        while r < self.mesh_rules.len:
            var mr = self.mesh_rules[r]
            if mr.src == li:
                var dstN = self.layers[mr.dst].get_neurons()
                var sN = self.layers[li].get_neurons()
                if new_idx >= 0 and new_idx < sN.len:
                    var s = sN[new_idx]
                    var j = 0
                    while j < dstN.len:
                        if self.rand_f64() <= mr.prob:
                            s.connect(j, mr.feedback)
                        j = j + 1
            r = r + 1

        # Inbound mesh: src -> this layer
        r = 0
        while r < self.mesh_rules.len:
            var mr2 = self.mesh_rules[r]
            if mr2.dst == li:
                var srcN = self.layers[mr2.src].get_neurons()
                var j = 0
                while j < srcN.len:
                    if self.rand_f64() <= mr2.prob:
                        srcN[j].connect(new_idx, mr2.feedback)
                    j = j + 1
            r = r + 1

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
            var neuron_list = self.layers[li3].get_neurons()
            var ni = 0
            while ni < neuron_list.len:
                metrics.add_slots(Int64(neuron_list[ni].slots.size()))
                metrics.add_synapses(Int64(neuron_list[ni].outgoing.size()))
                ni = ni + 1
            li3 = li3 + 1
        return metrics
