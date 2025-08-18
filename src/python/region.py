from region_bus import RegionBus
from layer import Layer
from tract import Tract
from input_layer_2d import InputLayer2D
from output_layer_2d import OutputLayer2D
from region_metrics import RegionMetrics

class RegionMetrics:
    def __init__(self):
        self.delivered_events = 0
        self.total_slots = 0
        self.total_synapses = 0

class PruneSummary:
    def __init__(self):
        self.pruned_synapses = 0
        self.pruned_edges = 0

class Region:
    def __init__(self, name):
        self.name = str(name)
        self.layers = []
        self.tracts = []
        self.bus = RegionBus()
        self.input_ports = {}
        self.output_ports = {}

    # construction
    def add_layer(self, excitatory_count, inhibitory_count, modulatory_count):
        layer = Layer(excitatory_count, inhibitory_count, modulatory_count)
        self.layers.append(layer)
        return len(self.layers) - 1

    def add_input_layer_2d(self, height, width, gain, epsilon_fire):
        layer = InputLayer2D(height, width, gain, epsilon_fire)
        self.layers.append(layer)
        return len(self.layers) - 1

    def add_output_layer_2d(self, height, width, smoothing):
        layer = OutputLayer2D(height, width, smoothing)
        self.layers.append(layer)
        return len(self.layers) - 1

    def connect_layers(self, source_index, dest_index, probability, feedback=False):
        if source_index < 0 or source_index >= len(self.layers):
            raise IndexError("source_index out of range")
        if dest_index < 0 or dest_index >= len(self.layers):
            raise IndexError("dest_index out of range")
        tract = Tract(self.layers[source_index], self.layers[dest_index], self.bus, feedback)
        self.tracts.append(tract)
        # intra-layer random wiring can still be requested externally if desired
        return tract

    def bind_input(self, port, layer_indices):
        self.input_ports[str(port)] = list(layer_indices)

    def bind_output(self, port, layer_indices):
        self.output_ports[str(port)] = list(layer_indices)

    # region-wide pulses
    def pulse_inhibition(self, factor):
        self.bus.set_inhibition_factor(factor)

    def pulse_modulation(self, factor):
        self.bus.set_modulation_factor(factor)



    def tick(self, port: str, value: float) -> "RegionMetrics":
        metrics = RegionMetrics()
        entry = self.input_ports.get(port)
        if entry is not None:
            for idx in entry:
                self.layers[idx].forward(value)
                metrics.inc_delivered_events()

        for layer in self.layers:
            layer.end_tick()

        for layer in self.layers:
            for neuron in layer.get_neurons():
                try:    slots = neuron.get_slots()
                except: slots = getattr(neuron, "slots", [])
                try:    outgoing = neuron.get_outgoing()
                except: outgoing = getattr(neuron, "outgoing", [])
                metrics.add_slots(len(slots))
                metrics.add_synapses(len(outgoing))
        return metrics

    def tick_image(self, port: str, frame: "list[list[float]]") -> "RegionMetrics":
        metrics = RegionMetrics()
        entry = self.input_ports.get(port)
        if entry is not None:
            for idx in entry:
                layer = self.layers[idx]
                if hasattr(layer, "forward_image"):
                    layer.forward_image(frame)
                    metrics.inc_delivered_events()

        for layer in self.layers:
            layer.end_tick()

        for layer in self.layers:
            for neuron in layer.get_neurons():
                try:    slots = neuron.get_slots()
                except: slots = getattr(neuron, "slots", [])
                try:    outgoing = neuron.get_outgoing()
                except: outgoing = getattr(neuron, "outgoing", [])
                metrics.add_slots(len(slots))
                metrics.add_synapses(len(outgoing))
        return metrics

    # maintenance
    def prune(self, synapse_stale_window=10_000, synapse_min_strength=0.05,
              tract_stale_window=10_000, tract_min_strength=0.05):
        # Lightweight placeholder; full pruning requires synapse timestamps, etc.
        return PruneSummary()

    # accessors
    def get_name(self):
        return self.name

    def get_layers(self):
        return self.layers

    def get_tracts(self):
        return self.tracts

    def get_bus(self):
        return self.bus
