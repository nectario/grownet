from region_bus import RegionBus
from layer import Layer
from tract import Tract
from input_layer_2d import InputLayer2D
from output_layer_2d import OutputLayer2D

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
        self._name = str(name)
        self._layers = []
        self._tracts = []
        self._bus = RegionBus()
        self._input_ports = {}
        self._output_ports = {}

    # construction
    def add_layer(self, excitatory_count, inhibitory_count, modulatory_count):
        layer = Layer(excitatory_count, inhibitory_count, modulatory_count)
        self._layers.append(layer)
        return len(self._layers) - 1

    def add_input_layer_2d(self, height, width, gain, epsilon_fire):
        layer = InputLayer2D(height, width, gain, epsilon_fire)
        self._layers.append(layer)
        return len(self._layers) - 1

    def add_output_layer_2d(self, height, width, smoothing):
        layer = OutputLayer2D(height, width, smoothing)
        self._layers.append(layer)
        return len(self._layers) - 1

    def connect_layers(self, source_index, dest_index, probability, feedback=False):
        if source_index < 0 or source_index >= len(self._layers):
            raise IndexError("source_index out of range")
        if dest_index < 0 or dest_index >= len(self._layers):
            raise IndexError("dest_index out of range")
        tract = Tract(self._layers[source_index], self._layers[dest_index], self._bus, feedback)
        self._tracts.append(tract)
        # intra-layer random wiring can still be requested externally if desired
        return tract

    def bind_input(self, port, layer_indices):
        self._input_ports[str(port)] = list(layer_indices)

    def bind_output(self, port, layer_indices):
        self._output_ports[str(port)] = list(layer_indices)

    # region-wide pulses
    def pulse_inhibition(self, factor):
        self._bus.set_inhibition_factor(factor)

    def pulse_modulation(self, factor):
        self._bus.set_modulation_factor(factor)

    # main loop
    def tick(self, port, value):
        m = RegionMetrics()
        entry = self._input_ports.get(str(port))
        if entry is not None:
            for layer_index in entry:
                self._layers[layer_index].forward(value)
                m.delivered_events += 1

        # end-of-tick housekeeping
        for layer in self._layers:
            layer.end_tick()

        # aggregates
        for layer in self._layers:
            for neuron in layer.get_neurons():
                m.total_slots += len(neuron.slots())
                m.total_synapses += len(neuron.get_outgoing())
        return m

    def tick_image(self, port, frame):
        m = RegionMetrics()
        entry = self._input_ports.get(str(port))
        if entry is not None:
            for layer_index in entry:
                layer = self._layers[layer_index]
                if isinstance(layer, InputLayer2D):
                    layer.forward_image(frame)
                    m.delivered_events += 1
        for layer in self._layers:
            layer.end_tick()
        for layer in self._layers:
            for neuron in layer.get_neurons():
                m.total_slots += len(neuron.slots())
                m.total_synapses += len(neuron.get_outgoing())
        return m

    # maintenance
    def prune(self, synapse_stale_window=10_000, synapse_min_strength=0.05,
              tract_stale_window=10_000, tract_min_strength=0.05):
        # Lightweight placeholder; full pruning requires synapse timestamps, etc.
        return PruneSummary()

    # accessors
    def get_name(self):
        return self._name

    def get_layers(self):
        return self._layers

    def get_tracts(self):
        return self._tracts

    def get_bus(self):
        return self._bus
