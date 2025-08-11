from slot_policy import SlotPolicyConfig
# layer.mojo
# Pool of neurons with a simple LateralBus and intra-layer connectivity managed here.

from neuron import Neuron
from weight import Weight
from math_utils import pseudo_random_pair

struct LateralBus:
    var inhibition_factor: Float64 = 1.0   # 1.0 => no inhibition
    var modulation_factor: Float64 = 1.0   # scales learning rate
    var current_step: Int64 = 0

    fn decay(self):
        self.inhibition_factor = 1.0
        self.modulation_factor = 1.0
        self.current_step = self.current_step + 1

# Edge type for within-layer connections (kept here to avoid cross-file ownership complexity)
struct LocalEdge:
    var target_index: Int64
    var weight: Weight = Weight()
    var last_step: Int64 = 0

struct Layer:
    var neurons: Array[Neuron] = Array()
    var bus: LateralBus = LateralBus()
    var adjacency: Dict[Int64, Array[LocalEdge]] = Dict()

    # Construction
    fn init(self, excitatory_count: Int64, inhibitory_count: Int64, modulatory_count: Int64):
        # Excitatory
        for i in range(excitatory_count):
            var n = Neuron(neuron_id=f"E{i}", kind="E")
            self.neurons.push(n)
        # Inhibitory
        for i in range(inhibitory_count):
            var n = Neuron(neuron_id=f"I{i}", kind="I")
            self.neurons.push(n)
        # Modulatory
        for i in range(modulatory_count):
            var n = Neuron(neuron_id=f"M{i}", kind="M")
            self.neurons.push(n)

    # Wiring helpers (deterministic pseudo-random; no external RNG dependency)
    fn wire_random_feedforward(self, probability: Float64):
        var n = Int64(self.neurons.len)
        for i in range(n):
            for j in range(n):
                if i == j:
                    continue
                var r = pseudo_random_pair(Int64(i + 7), Int64(j + 13))
                if r < probability:
                    if not self.adjacency.contains(Int64(i)):
                        self.adjacency[Int64(i)] = Array[LocalEdge]()
                    var edge = LocalEdge(target_index=Int64(j))
                    self.adjacency[Int64(i)].push(edge)

    fn wire_random_feedback(self, probability: Float64):
        # same method; semantically "feedback", still within-layer for simplicity
        self.wire_random_feedforward(probability)

    # Internal propagation from one source index (used by both forward() and Region tract delivery)
    fn propagate_from(self, src_index: Int64, value: Float64):
        if not self.adjacency.contains(src_index):
            return
        var edges = self.adjacency[src_index]
        for e in edges:
            e.weight.reinforce(self.bus.modulation_factor, self.bus.inhibition_factor)
            var fired = e.weight.update_threshold(value)
            e.last_step = self.bus.current_step
            if fired:
                # Inject into target neuron (local hop) and allow cascade limited to target's outgoing
                var target = e.target_index
                var fired_target = self.neurons[Int64(target)].on_input(value, self.bus.modulation_factor, self.bus.inhibition_factor)
                if fired_target:
                    # optional: one-level cascade
                    if self.adjacency.contains(Int64(target)):
                        var next_edges = self.adjacency[Int64(target)]
                        for ne in next_edges:
                            ne.weight.reinforce(self.bus.modulation_factor, self.bus.inhibition_factor)
                            var fired2 = ne.weight.update_threshold(value)
                            ne.last_step = self.bus.current_step
                            if fired2:
                                var t2 = ne.target_index
                                _ = self.neurons[Int64(t2)].on_input(value, self.bus.modulation_factor, self.bus.inhibition_factor)

    # Main entry for an external scalar at the layer level
    fn forward(self, value: Float64):
        var fired_indices = Array[Int64]()
        for i in range(Int64(self.neurons.len)):
            var neuron = self.neurons[i]
            var fired = neuron.on_input(value, self.bus.modulation_factor, self.bus.inhibition_factor)
            if fired:
                fired_indices.push(i)
                # apply one-tick bus effects based on neuron kind
                if neuron.kind == "I":
                    self.bus.inhibition_factor = 0.7
                elif neuron.kind == "M":
                    self.bus.modulation_factor = 1.5

        # After scanning, propagate from fired sources through adjacency
        for idx in fired_indices:
            self.propagate_from(idx, value)

    # Maintenance
    fn prune_synapses(self, current_step: Int64, stale_window: Int64, min_strength: Float64) -> Int64:
        var pruned = 0
        for key in self.adjacency.keys():
            var edges = self.adjacency[key]
            var kept = Array[LocalEdge]()
            for e in edges:
                var stale = (current_step - e.last_step) > stale_window
                var weak = e.weight.strength_value < min_strength
                if stale and weak:
                    pruned = pruned + 1
                else:
                    kept.push(e)
            self.adjacency[key] = kept
        return pruned

    fn set_slot_policy(inout self, policy: SlotPolicyConfig):
        self.slot_policy = policy
