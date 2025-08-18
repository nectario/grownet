from typing import List, Dict, Optional
from region_bus import RegionBus
from region_metrics import RegionMetrics
from layer import Layer
from input_layer_2d import InputLayer2D
from output_layer_2d import OutputLayer2D
from neuron import Neuron

class PruneSummary:
    def __init__(self) -> None:
        self.pruned_synapses: int = 0
        self.pruned_edges: int = 0

class Region:
    """
    Python mirror of the Java/C++ Region API with snake_case names.
    No legacy fields; metrics and signals are explicit.
    """
    def __init__(self, name: str) -> None:
        self._name = str(name)
        self._layers: List[object] = []
        self._input_ports: Dict[str, List[int]] = {}
        self._output_ports: Dict[str, List[int]] = {}
        self._bus = RegionBus()

    # ------------- construction -------------
    def add_layer(self, excitatory_count: int, inhibitory_count: int, modulatory_count: int) -> int:
        layer = Layer(excitatory_count, inhibitory_count, modulatory_count, self._bus)
        self._layers.append(layer)
        return len(self._layers) - 1

    def add_input_layer_2d(self, height: int, width: int, gain: float, epsilon_fire: float) -> int:
        layer = InputLayer2D(height, width, gain, epsilon_fire, self._bus)
        self._layers.append(layer)
        return len(self._layers) - 1

    def add_output_layer_2d(self, height: int, width: int, smoothing: float) -> int:
        layer = OutputLayer2D(height, width, smoothing, self._bus)
        self._layers.append(layer)
        return len(self._layers) - 1

    # ------------- wiring -------------
    def connect_layers(self, source_index: int, dest_index: int, probability: float, feedback: bool=False) -> int:
        import random
        if source_index < 0 or source_index >= len(self._layers):
            raise IndexError("source_index out of range")
        if dest_index < 0 or dest_index >= len(self._layers):
            raise IndexError("dest_index out of range")
        p = max(0.0, min(1.0, float(probability)))

        src = self._layers[source_index]
        dst = self._layers[dest_index]
        edges = 0
        src_neurons: List[Neuron] = src.get_neurons()
        dst_neurons: List[Neuron] = dst.get_neurons()
        for a in src_neurons:
            for b in dst_neurons:
                if a is b: 
                    continue
                if random.random() < p:
                    a.connect(b, feedback=feedback)
                    edges += 1
        return edges

    def bind_input(self, port: str, layer_indices: List[int]) -> None:
        self._input_ports[str(port)] = list(layer_indices)

    def bind_output(self, port: str, layer_indices: List[int]) -> None:
        self._output_ports[str(port)] = list(layer_indices)

    # ------------- bus pulses -------------
    def pulse_inhibition(self, factor: float) -> None:
        self._bus.set_inhibition_factor(factor)

    def pulse_modulation(self, factor: float) -> None:
        self._bus.set_modulation_factor(factor)

    # ------------- tick (scalar) -------------
    def tick(self, port: str, value: float) -> RegionMetrics:
        metrics = RegionMetrics()
        entry = self._input_ports.get(port)
        if entry is not None:
            for idx in entry:
                self._layers[idx].forward(value)
                metrics.inc_delivered_events()
        # end-of-tick
        for layer in self._layers:
            layer.end_tick()
        # aggregates
        for layer in self._layers:
            for neuron in layer.get_neurons():
                metrics.add_slots(len(neuron.get_slots()))
                metrics.add_synapses(len(neuron.get_outgoing()))
        return metrics

    # ------------- tick (image) -------------
    def tick_image(self, port: str, frame: "list[list[float]]") -> RegionMetrics:
        metrics = RegionMetrics()
        entry = self._input_ports.get(port)
        if entry is not None:
            for idx in entry:
                layer = self._layers[idx]
                if isinstance(layer, InputLayer2D):
                    layer.forward_image(frame)
                    metrics.inc_delivered_events()
        for layer in self._layers:
            layer.end_tick()
        for layer in self._layers:
            for neuron in layer.get_neurons():
                metrics.add_slots(len(neuron.get_slots()))
                metrics.add_synapses(len(neuron.get_outgoing()))
        return metrics

    # ------------- prune (placeholder) -------------
    def prune(self, synapse_stale_window: int, synapse_min_strength: float) -> PruneSummary:
        # This simplified mirror doesn't track staleness/strength; keep the API stable.
        return PruneSummary()

    # ------------- accessors -------------
    def get_name(self) -> str:
        return self._name

    def get_layers(self) -> List[object]:
        return self._layers

    def get_bus(self) -> RegionBus:
        return self._bus
