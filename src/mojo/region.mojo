# region.mojo
# Region (group of layers) with Tracts (inter-layer bundles) and a two-phase tick.

from layer import Layer, LateralBus
from neuron import Neuron
from weight import Weight
from math_utils import pseudo_random_pair

struct RegionBus:
    var inhibition_factor: Float64 = 1.0
    var modulation_factor: Float64 = 1.0
    var current_step: Int64 = 0

    fn decay(self):
        self.inhibition_factor = 1.0
        self.modulation_factor = 1.0
        self.current_step = self.current_step + 1

struct InterLayerEdge:
    var target_index: Int64
    var weight: Weight = Weight()
    var is_feedback: Bool = False
    var last_step: Int64 = 0

struct QueuedEvent:
    var target_index: Int64
    var value: Float64

struct Tract:
    var source: Layer
    var destination: Layer
    var region_bus: RegionBus
    var is_feedback: Bool = False

    var edges: Dict[Int64, Array[InterLayerEdge]] = Dict()
    var queue: Array[QueuedEvent] = Array()

    fn wire_dense_random(self, probability: Float64):
        var ns = Int64(self.source.neurons.len)
        var nd = Int64(self.destination.neurons.len)
        for i in range(ns):
            for j in range(nd):
                var r = pseudo_random_pair(i + 101, j + 211)
                if r < probability:
                    if not self.edges.contains(i):
                        self.edges[i] = Array[InterLayerEdge]()
                    var e = InterLayerEdge(target_index=Int64(j), is_feedback=self.is_feedback)
                    self.edges[i].push(e)

    fn collect_from_sources(self):
        # Build a per-tick queue based on source neurons that fired in Phase A
        for i in range(Int64(self.source.neurons.len)):
            var n = self.source.neurons[i]
            if not n.fired_last:
                continue
            if not self.edges.contains(i):
                continue
            var edges = self.edges[i]
            for e in edges:
                e.weight.reinforce(self.region_bus.modulation_factor, self.region_bus.inhibition_factor)
                var fired = e.weight.update_threshold(n.last_input_value)
                e.last_step = self.region_bus.current_step
                if fired:
                    var ev = QueuedEvent(target_index=e.target_index, value=n.last_input_value)
                    self.queue.push(ev)

    fn flush(self) -> Int64:
        var delivered = 0
        if self.queue.len == 0:
            return delivered
        var pending = self.queue
        self.queue = Array[QueuedEvent]()
        for ev in pending:
            # Inject into destination layer at target index; allow local propagation
            self.destination.propagate_from(ev.target_index, ev.value)
            delivered = delivered + 1
        return delivered

    fn prune_edges(self, stale_window: Int64, min_strength: Float64) -> Int64:
        var pruned = 0
        for key in self.edges.keys():
            var vec = self.edges[key]
            var kept = Array[InterLayerEdge]()
            for e in vec:
                var stale = (self.region_bus.current_step - e.last_step) > stale_window
                var weak  = e.weight.strength_value < min_strength
                if stale and weak:
                    pruned = pruned + 1
                else:
                    kept.push(e)
            self.edges[key] = kept
        return pruned

struct RegionMetrics:
    var delivered_events: Int64
    var total_slots: Int64
    var total_synapses: Int64

struct PruneSummary:
    var pruned_synapses: Int64
    var pruned_edges: Int64

struct Region:
    var name: String
    var layers: Array[Layer] = Array()
    var tracts: Array[Tract] = Array()
    var bus: RegionBus = RegionBus()
    var input_ports: Dict[String, Array[Int64]] = Dict()
    var output_ports: Dict[String, Array[Int64]] = Dict()

    fn add_layer(self, excitatory_count: Int64, inhibitory_count: Int64, modulatory_count: Int64) -> Int64:
        var l = Layer()
        l.init(excitatory_count, inhibitory_count, modulatory_count)
        self.layers.push(l)
        return Int64(self.layers.len) - 1

    fn connect_layers(self, source_index: Int64, dest_index: Int64, probability: Float64, feedback: Bool = False) -> Tract:
        var src = self.layers[source_index]
        var dst = self.layers[dest_index]
        var t = Tract(source=src, destination=dst, region_bus=self.bus, is_feedback=feedback)
        t.wire_dense_random(probability)
        self.tracts.push(t)
        return t

    fn bind_input(self, port: String, layer_indices: Array[Int64]):
        self.input_ports[port] = layer_indices

    fn bind_output(self, port: String, layer_indices: Array[Int64]):
        self.output_ports[port] = layer_indices

    fn pulse_inhibition(self, factor: Float64):
        self.bus.inhibition_factor = factor

    fn pulse_modulation(self, factor: Float64):
        self.bus.modulation_factor = factor

    fn tick(self, port: String, value: Float64) -> RegionMetrics:
        # Phase A: external input to entry layers (intra-layer propagation occurs immediately)
        if self.input_ports.contains(port):
            var entries = self.input_ports[port]
            for idx in entries:
                self.layers[idx].forward(value)

        # Collect from fired sources
        for t in self.tracts:
            t.collect_from_sources()

        # Phase B: flush inter-layer tracts once
        var delivered = 0
        for t in self.tracts:
            delivered = delivered + t.flush()

        # Decay
        for l in self.layers:
            l.bus.decay()
        self.bus.decay()

        # Metrics
        var total_slots = 0
        var total_synapses = 0
        for l in self.layers:
            for n in l.neurons:
                total_slots = total_slots + Int64(n.slots.len)
                # approximate synapse count by adjacency sum
            for key in l.adjacency.keys():
                total_synapses = total_synapses + Int64(l.adjacency[key].len)

        return RegionMetrics(delivered_events=delivered, total_slots=total_slots, total_synapses=total_synapses)

    fn prune(self, synapse_stale_window: Int64 = 10_000, synapse_min_strength: Float64 = 0.05,
                   tract_stale_window: Int64 = 10_000, tract_min_strength: Float64 = 0.05) -> PruneSummary:
        var pruned_syn = 0
        for l in self.layers:
            pruned_syn = pruned_syn + l.prune_synapses(self.bus.current_step, synapse_stale_window, synapse_min_strength)
        var pruned_edges = 0
        for t in self.tracts:
            pruned_edges = pruned_edges + t.prune_edges(tract_stale_window, tract_min_strength)
        return PruneSummary(pruned_synapses=pruned_syn, pruned_edges=pruned_edges)
