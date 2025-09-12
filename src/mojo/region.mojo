# src/mojo/region.mojo — Mojo Region implementation (Python-parity: snake_case)

from region_metrics import RegionMetrics
from layer import Layer
from input_layer_2d import InputLayer2D
from input_layer_nd import InputLayerND
from output_layer_2d import OutputLayer2D
from region_bus import RegionBus
from growth_policy import GrowthPolicy
from growth_engine import maybe_grow
from synapse import Synapse
from tract import Tract
from policy.proximity_connectivity import ProximityConfig, ProximityEngine

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
    var tracts: list[Tract]
    var enable_spatial_metrics: Bool
    var rng_state: UInt64
    var output_layer_indices: list[Int]
    var growth_policy: GrowthPolicy
    var growth_policy_enabled: Bool
    var last_layer_growth_step: Int
    var proximity_config: ProximityConfig

    fn init(mut self, name: String) -> None:
        self.name = name
        self.layers = []
        self.input_ports = dict[String, list[Int]]()
        self.output_ports = dict[String, list[Int]]()
        self.input_edges = dict[String, Int]()
        self.output_edges = dict[String, Int]()
        self.bus = RegionBus()
        self.mesh_rules = []
        self.tracts = []
        self.enable_spatial_metrics = False
        self.rng_state = 0x9E3779B97F4A7C15
        self.output_layer_indices = []
        self.growth_policy = GrowthPolicy()
        self.growth_policy_enabled = False
        self.last_layer_growth_step = -1
        self.proximity_config = ProximityConfig()

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
        if new_layer.set_region is not None:
            new_layer.set_region(self)
        self.layers.append(new_layer)
        return self.layers.len - 1

    fn add_input_layer_2d(mut self, height: Int, width: Int, gain: Float64, epsilon_fire: Float64) -> Int:
        var new_input_layer = InputLayer2D(height, width, gain, epsilon_fire)
        self.layers.append(new_input_layer)
        return self.layers.len - 1

    fn add_input_layer_nd(mut self, shape: list[Int], gain: Float64, epsilon_fire: Float64) -> Int:
        var new_input_nd = InputLayerND(shape, gain, epsilon_fire)
        self.layers.append(new_input_nd)
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

    # ---------------- pulses (parity with Python/Java) ----------------
    fn pulse_inhibition(mut self, factor: Float64) -> None:
        self.bus.set_inhibition_factor(factor)
        var li = 0
        while li < self.layers.len:
            self.layers[li].bus.set_inhibition_factor(factor)
            li = li + 1

    fn pulse_modulation(mut self, factor: Float64) -> None:
        self.bus.set_modulation_factor(factor)
        var lj = 0
        while lj < self.layers.len:
            self.layers[lj].bus.set_modulation_factor(factor)
            lj = lj + 1

    # ---------------- ensure edge helpers (public) ----------------
    fn ensure_input_edge(mut self, port: String, neurons: Int = 1) -> Int:
        if self.input_edges.contains(port):
            return self.input_edges[port]
        _ = neurons  # reserved; scalar edge is 1-neuron layer
        var edge_index = self.add_layer(1, 0, 0)
        self.input_edges[port] = edge_index
        return edge_index

    fn ensure_output_edge(mut self, port: String, neurons: Int = 1) -> Int:
        if self.output_edges.contains(port):
            return self.output_edges[port]
        _ = neurons
        var edge_index = self.add_layer(1, 0, 0)
        self.output_edges[port] = edge_index
        return edge_index

    # ---------------- prune (stub parity) ----------------
    struct PruneSummary:
        var pruned_synapses: Int64 = 0
        var pruned_edges: Int64 = 0

    fn prune(self, synapse_stale_window: Int64, synapse_min_strength: Float64) -> PruneSummary:
        _ = synapse_stale_window; _ = synapse_min_strength
        return PruneSummary()

    # ---------------- spatial metrics (helper) ----------------
    fn compute_spatial_metrics(self, img: list[list[Float64]], prefer_output: Bool = true) -> RegionMetrics:
        var metrics = RegionMetrics()
        var chosen = img
        if prefer_output and self.output_layer_indices.len > 0:
            var pick = self.output_layer_indices[self.output_layer_indices.len - 1]
            if pick >= 0 and pick < self.layers.len:
                if hasattr(self.layers[pick], "get_frame"):
                    var out = (self.layers[pick] as OutputLayer2D).get_frame()
                    # prefer out if non-zero; else use input
                    if _has_non_zero(out):
                        chosen = out
        var active: Int64 = 0
        var total: Float64 = 0.0
        var sum_r: Float64 = 0.0
        var sum_c: Float64 = 0.0
        var rmin: Int64 = 1000000000
        var rmax: Int64 = -1
        var cmin: Int64 = 1000000000
        var cmax: Int64 = -1
        var H = chosen.len
        var W = (H > 0) ? chosen[0].len : 0
        var r = 0
        while r < H:
            var row = chosen[r]
            var c = 0
            var Wc = (W < row.len) ? W : row.len
            while c < Wc:
                var v = row[c]
                if v > 0.0:
                    active = active + 1
                    total = total + v
                    sum_r = sum_r + (Float64)(r) * v
                    sum_c = sum_c + (Float64)(c) * v
                    if r < rmin: rmin = r
                    if r > rmax: rmax = r
                    if c < cmin: cmin = c
                    if c > cmax: cmax = c
                c = c + 1
            r = r + 1
        metrics.active_pixels = active
        if total > 0.0:
            metrics.centroid_row = sum_r / total
            metrics.centroid_col = sum_c / total
        else:
            metrics.centroid_row = 0.0
            metrics.centroid_col = 0.0
        if rmax >= rmin and cmax >= cmin:
            metrics.set_bbox(rmin, rmax, cmin, cmax)
        else:
            metrics.set_bbox(0, -1, 0, -1)
        return metrics

    fn _has_non_zero(img: list[list[Float64]]) -> Bool:
        var i = 0
        while i < img.len:
            var row = img[i]
            var j = 0
            while j < row.len:
                if row[j] != 0.0: return true
                j = j + 1
            i = i + 1
        return false

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
                    source_neurons[source_counter].connect(dest_counter, feedback)
                    edge_count = edge_count + 1
                dest_counter = dest_counter + 1
            source_counter = source_counter + 1
        self.mesh_rules.append(MeshRule(source_index, dest_index, probability, feedback))
        return edge_count

    # Windowed deterministic wiring (Python/C++ parity)
    fn connect_layers_windowed(mut self,
                               src_index: Int,
                               dest_index: Int,
                               kernel_h: Int,
                               kernel_w: Int,
                               stride_h: Int = 1,
                               stride_w: Int = 1,
                               padding: String = "valid",
                               feedback: Bool = False) -> Int:
        if src_index < 0 or src_index >= self.layers.len: raise Error("src_index out of range")
        if dest_index < 0 or dest_index >= self.layers.len: raise Error("dest_index out of range")
        var source_layer = self.layers[src_index]
        var dest_layer = self.layers[dest_index]
        if not hasattr(source_layer, "height") or not hasattr(source_layer, "width"):
            raise Error("connect_layers_windowed requires src to be InputLayer2D")
        var source_height = source_layer.height
        var source_width = source_layer.width
        var kernel_height = if kernel_h > 0 then kernel_h else 1
        var kernel_width = if kernel_w > 0 then kernel_w else 1
        var stride_height = if stride_h > 0 then stride_h else 1
        var stride_width = if stride_w > 0 then stride_w else 1
        var use_same = (padding == "same") or (padding == "SAME")

        var origins: list[tuple[Int, Int]] = []
        if use_same:
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
            var origin_row_valid = 0
            while origin_row_valid + kernel_height <= source_height:
                var origin_col_valid = 0
                while origin_col_valid + kernel_width <= source_width:
                    origins.append((origin_row_valid, origin_col_valid))
                    origin_col_valid = origin_col_valid + stride_width
                origin_row_valid = origin_row_valid + stride_height

        var allowed_sources = dict[Int, Bool]()
        var dest_is_output = hasattr(dest_layer, "height") and hasattr(dest_layer, "width")
        if dest_is_output:
            var dest_height = dest_layer.height
            var dest_width = dest_layer.width
            var seen: dict[tuple[Int, Int], Bool] = dict[tuple[Int, Int], Bool]()
            var origin_index_center = 0
            while origin_index_center < origins.len:
                var origin_row = origins[origin_index_center][0]
                var origin_col = origins[origin_index_center][1]
                var row_start = if origin_row > 0 then origin_row else 0
                var col_start = if origin_col > 0 then origin_col else 0
                var row_end = if (origin_row + kernel_height) < source_height then (origin_row + kernel_height) else source_height
                var col_end = if (origin_col + kernel_width) < source_width then (origin_col + kernel_width) else source_width
                if row_start < row_end and col_start < col_end:
                    var center_row = origin_row + (kernel_height / 2)
                    if center_row < 0: center_row = 0
                    if center_row > (dest_height - 1): center_row = dest_height - 1
                    var center_col = origin_col + (kernel_width / 2)
                    if center_col < 0: center_col = 0
                    if center_col > (dest_width - 1): center_col = dest_width - 1
                    var center_index = center_row * dest_width + center_col
                    var row_iter_center = row_start
                    while row_iter_center < row_end:
                        var col_iter_center = col_start
                        while col_iter_center < col_end:
                            var sidx = row_iter_center * source_width + col_iter_center
                            allowed_sources[sidx] = True
                            var edge_key = (sidx, center_index)
                            if not seen.contains(edge_key):
                                self.layers[src_index].get_neurons()[sidx].connect(center_index, feedback)
                                seen[edge_key] = True
                            col_iter_center = col_iter_center + 1
                        row_iter_center = row_iter_center + 1
                origin_index_center = origin_index_center + 1
            # Register tract for growth re-attach
            var tract_out2d = Tract(src_index, dest_index,
                                    kernel_height, kernel_width,
                                    stride_height, stride_width,
                                    use_same, feedback,
                                    source_height, source_width,
                                    dest_height, dest_width)
            self.tracts.append(tract_out2d)
            return Int(allowed_sources.size())

        # generic destination: unique sources connect to all dest neurons
        var origin_index_generic = 0
        while origin_index_generic < origins.len:
            var origin_row_generic = origins[origin_index_generic][0]
            var origin_col_generic = origins[origin_index_generic][1]
            var row_start_generic = if origin_row_generic > 0 then origin_row_generic else 0
            var col_start_generic = if origin_col_generic > 0 then origin_col_generic else 0
            var row_end_generic = if (origin_row_generic + kernel_height) < source_height then (origin_row_generic + kernel_height) else source_height
            var col_end_generic = if (origin_col_generic + kernel_width) < source_width then (origin_col_generic + kernel_width) else source_width
            if row_start_generic < row_end_generic and col_start_generic < col_end_generic:
                var row_iter_generic = row_start_generic
                while row_iter_generic < row_end_generic:
                    var col_iter_generic = col_start_generic
                    while col_iter_generic < col_end_generic:
                        var flat = row_iter_generic * source_width + col_iter_generic
                        allowed_sources[flat] = True
                        col_iter_generic = col_iter_generic + 1
                    row_iter_generic = row_iter_generic + 1
            origin_index_generic = origin_index_generic + 1
        var dst_neurons = dest_layer.get_neurons()
        for src_flat in allowed_sources.keys():
            var dest_neuron_index = 0
            while dest_neuron_index < dst_neurons.len:
                self.layers[src_index].get_neurons()[src_flat].connect(dest_neuron_index, feedback)
                dest_neuron_index = dest_neuron_index + 1
        var tract_generic = Tract(src_index, dest_index,
                                  kernel_height, kernel_width,
                                  stride_height, stride_width,
                                  use_same, feedback,
                                  source_height, source_width,
                                  1, 1)
        self.tracts.append(tract_generic)
        return Int(allowed_sources.size())

    # ---------------- edge helpers ----------------
    fn ensure_input_edge(mut self, port: String) -> Int:
        if self.input_edges.contains(port):
            return self.input_edges[port]
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
        var bind_index = 0
        while bind_index < layer_indices.len:
            self.connect_layers(edge, layer_indices[bind_index], 1.0, False)
            bind_index = bind_index + 1

    fn bind_input_2d(mut self, port: String, height: Int, width: Int, gain: Float64, epsilon_fire: Float64, layer_indices: list[Int]) -> None:
        var edge = self.ensure_input_edge(port)
        var layer_ref = self.layers[edge]
        if hasattr(layer_ref, "height") and hasattr(layer_ref, "width") and layer_ref.height == height and layer_ref.width == width:
            # reuse
            pass
        else:
            var new_edge = self.add_input_layer_2d(height, width, gain, epsilon_fire)
            self.input_edges[port] = new_edge
            edge = new_edge
        var attach_index = 0
        while attach_index < layer_indices.len:
            self.connect_layers(edge, layer_indices[attach_index], 1.0, False)
            attach_index = attach_index + 1

    fn bind_output(mut self, port: String, layer_indices: list[Int]) -> None:
        self.output_ports[port] = layer_indices
        var edge = self.ensure_output_edge(port)
        var output_attach_index = 0
        while output_attach_index < layer_indices.len:
            self.connect_layers(layer_indices[output_attach_index], edge, 1.0, False)
            output_attach_index = output_attach_index + 1

    fn bind_input_nd(mut self, port: String, shape: list[Int], gain: Float64, epsilon_fire: Float64, layer_indices: list[Int]) -> None:
        var edge = self.ensure_input_edge(port)
        var new_edge = self.add_input_layer_nd(shape, gain, epsilon_fire)
        self.input_edges[port] = new_edge
        var nd_attach_index = 0
        while nd_attach_index < layer_indices.len:
            self.connect_layers(new_edge, layer_indices[nd_attach_index], 1.0, False)
            nd_attach_index = nd_attach_index + 1

    # ---------------- ticks ----------------
    fn tick(mut self, port: String, value: Float64) -> RegionMetrics:
        var metrics = RegionMetrics()
        if not self.input_edges.contains(port):
            raise Error("No InputEdge for port '" + port + "'. Call bind_input(...) first.")
        var edge_idx = self.input_edges[port]
        self.layers[edge_idx].forward(value)
        # Optional proximity connectivity (post-propagation, pre end_tick/decay)
        if self.proximity_config.proximity_connect_enabled:
            var prox = ProximityEngine()
            _ = prox.apply(self, self.proximity_config)
        metrics.inc_delivered_events(1)

        var layer_index_end = 0
        while layer_index_end < self.layers.len:
            self.layers[layer_index_end].end_tick()
            layer_index_end = layer_index_end + 1
        self.bus.decay()

        var layer_index_aggregate = 0
        while layer_index_aggregate < self.layers.len:
            var neuron_list = self.layers[layer_index_aggregate].get_neurons()
            var neuron_index = 0
            while neuron_index < neuron_list.len:
                metrics.add_slots(Int64(neuron_list[neuron_index].slots.size()))
                metrics.add_synapses(Int64(neuron_list[neuron_index].outgoing.size()))
                neuron_index = neuron_index + 1
            layer_index_aggregate = layer_index_aggregate + 1

        if self.growth_policy_enabled:
            _ = maybe_grow(self, self.growth_policy)
        return metrics

    fn tick_2d(mut self, port: String, frame: list[list[Float64]]) -> RegionMetrics:
        var metrics = RegionMetrics()
        if not self.input_edges.contains(port):
            raise Error("No InputEdge for port '" + port + "'. Call bind_input_2d(...) first.")
        var edge_idx = self.input_edges[port]
        self.layers[edge_idx].forward_image(frame)
        # Optional proximity connectivity (post-propagation, pre end_tick/decay)
        if self.proximity_config.proximity_connect_enabled:
            var prox2 = ProximityEngine()
            _ = prox2.apply(self, self.proximity_config)
        metrics.inc_delivered_events(1)

        var layer_index_tick = 0
        while layer_index_tick < self.layers.len:
            self.layers[layer_index_tick].end_tick()
            layer_index_tick = layer_index_tick + 1
        self.bus.decay()

        var layer_index_aggregate2 = 0
        while layer_index_aggregate2 < self.layers.len:
            var list_neurons = self.layers[layer_index_aggregate2].get_neurons()
            var neuron_index2 = 0
            while neuron_index2 < list_neurons.len:
                metrics.add_slots(Int64(list_neurons[neuron_index2].slots.size()))
                metrics.add_synapses(Int64(list_neurons[neuron_index2].outgoing.size()))
                neuron_index2 = neuron_index2 + 1
            layer_index_aggregate2 = layer_index_aggregate2 + 1

        # spatial metrics (optional)
        if self.enable_spatial_metrics and self.output_layer_indices.len > 0:
            var out_idx = self.output_layer_indices[self.output_layer_indices.len - 1]
            var out = self.layers[out_idx]
            if hasattr(out, "pixels") and hasattr(out, "height") and hasattr(out, "width"):
                var image_height = out.height
                var image_width = out.width
                var active: Int64 = 0
                var total: Float64 = 0.0
                var sum_r: Float64 = 0.0
                var sum_c: Float64 = 0.0
                var rmin = image_height
                var rmax = -1
                var cmin = image_width
                var cmax = -1
                var row_iter = 0
                while row_iter < image_height:
                    var col_iter = 0
                    while col_iter < image_width:
                        var pixel_value = out.pixels[row_iter][col_iter]
                        if pixel_value != 0.0:
                            active = active + 1
                            total = total + pixel_value
                            sum_r = sum_r + Float64(row_iter) * pixel_value
                            sum_c = sum_c + Float64(col_iter) * pixel_value
                            if row_iter < rmin: rmin = row_iter
                            if row_iter > rmax: rmax = row_iter
                            if col_iter < cmin: cmin = col_iter
                            if col_iter > cmax: cmax = col_iter
                        col_iter = col_iter + 1
                    row_iter = row_iter + 1
                metrics.active_pixels = active
                if total > 0.0:
                    metrics.centroid_row = sum_r / total
                    metrics.centroid_col = sum_c / total
                else:
                    metrics.centroid_row = 0.0
                    metrics.centroid_col = 0.0
                if rmax >= rmin and cmax >= cmin:
                    metrics.set_bbox(rmin, rmax, cmin, cmax)
                else:
                    metrics.set_bbox(0, -1, 0, -1)
        if self.growth_policy_enabled:
            _ = maybe_grow(self, self.growth_policy)
        return metrics

    fn tick_image(mut self, port: String, frame: list[list[Float64]]) -> RegionMetrics:
        return self.tick_2d(port, frame)

    fn tick_nd(mut self, port: String, flat: list[Float64], shape: list[Int]) -> RegionMetrics:
        var metrics = RegionMetrics()
        if not self.input_edges.contains(port):
            raise Error("No InputEdge for port '" + port + "'. Call bind_input_nd(...) first.")
        var edge_idx = self.input_edges[port]
        self.layers[edge_idx].forward_nd(flat, shape)
        metrics.inc_delivered_events(1)
        var layer_index_end_nd = 0
        while layer_index_end_nd < self.layers.len:
            self.layers[layer_index_end_nd].end_tick()
            layer_index_end_nd = layer_index_end_nd + 1
        self.bus.decay()
        var layer_index_nd = 0
        while layer_index_nd < self.layers.len:
            var neurons = self.layers[layer_index_nd].get_neurons()
            var neuron_index_nd = 0
            while neuron_index_nd < neurons.len:
                metrics.add_slots(Int64(neurons[neuron_index_nd].slots.size()))
                metrics.add_synapses(Int64(neurons[neuron_index_nd].outgoing.size()))
                neuron_index_nd = neuron_index_nd + 1
            layer_index_nd = layer_index_nd + 1
        return metrics

    # -------- autowiring for grown neurons (by layer ref) --------
    fn autowire_new_neuron_by_ref(mut self, layer_ref: any, new_idx: Int) -> None:
        var layer_index = -1
        var search_index = 0
        while search_index < self.layers.len:
            if self.layers[search_index] == layer_ref:
                layer_index = search_index
                break
            search_index = search_index + 1
        if layer_index < 0: return
        # Outbound
        var rule_index = 0
        while rule_index < self.mesh_rules.len:
            var rule = self.mesh_rules[rule_index]
            if rule.src == layer_index:
                var dst_neurons = self.layers[rule.dst].get_neurons()
                var dest_neuron_index = 0
                while dest_neuron_index < dst_neurons.len:
                    if self.rand_f64() <= rule.prob:
                        self.layers[layer_index].get_neurons()[new_idx].connect(dest_neuron_index, rule.feedback)
                    dest_neuron_index = dest_neuron_index + 1
            rule_index = rule_index + 1
        # Inbound
        var rule_index_inbound = 0
        while rule_index_inbound < self.mesh_rules.len:
            var rule2 = self.mesh_rules[rule_index_inbound]
            if rule2.dst == layer_index:
                var src_neurons = self.layers[rule2.src].get_neurons()
                var src_index = 0
                while src_index < src_neurons.len:
                    if self.rand_f64() <= rule2.prob:
                        src_neurons[src_index].connect(new_idx, rule2.feedback)
                    src_index = src_index + 1
            rule_index_inbound = rule_index_inbound + 1

        # Windowed tracts: if this layer is a source, attach grown neuron
        var tract_index = 0
        while tract_index < self.tracts.len:
            var tract_obj = self.tracts[tract_index]
            if tract_obj.src_layer_index == layer_index:
                _ = tract_obj.attach_source_neuron(self, new_idx)
            tract_index = tract_index + 1

    # Request a spillover layer and wire deterministically
    fn request_layer_growth(mut self, layerRef: any, connection_probability: Float64 = 1.0) -> Int:
        var layer_index_ref = -1
        var search_index2 = 0
        while search_index2 < self.layers.len:
            if self.layers[search_index2] == layerRef:
                layer_index_ref = search_index2
                break
            search_index2 = search_index2 + 1
        if layer_index_ref < 0: return -1
        var new_index = self.add_layer(4, 0, 0)
        _ = self.connect_layers(layer_index_ref, new_index, connection_probability, False)
        return new_index
