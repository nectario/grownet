# region.py — Python Region implementation (clean, parity-focused)
from typing import List, Dict, Optional
import random
from metrics import RegionMetrics

# Layer and shape-aware layers are imported lazily to avoid import cycles.

class Region:
    class PruneSummary:
        def __init__(self):
            self.prunedSynapses = 0
            self.prunedEdges = 0  # reserved

    def __init__(self, name: str):
        self.name: str = name
        self.layers: List[object] = []
        self.input_ports: Dict[str, List[int]] = {}
        self.output_ports: Dict[str, List[int]] = {}
        self.bus = None   # RegionBus placeholder (future use)
        self.rng = random.Random(1234)

    # ---------------- construction ----------------
    def add_layer(self, excitatory_count: int, inhibitory_count: int, modulatory_count: int) -> int:
        from layer import Layer
        layer = Layer(excitatory_count, inhibitory_count, modulatory_count)
        self.layers.append(layer)
        return len(self.layers) - 1

    def add_input_layer_2d(self, height: int, width: int, gain: float, epsilon_fire: float) -> int:
        from input_layer_2d import InputLayer2D
        layer = InputLayer2D(height, width, gain, epsilon_fire)
        self.layers.append(layer)
        return len(self.layers) - 1

    def add_output_layer_2d(self, height: int, width: int, smoothing: float) -> int:
        from output_layer_2d import OutputLayer2D
        layer = OutputLayer2D(height, width, smoothing)
        self.layers.append(layer)
        return len(self.layers) - 1

    # ---------------- wiring ----------------
    def connect_layers(self, source_index: int, dest_index: int, probability: float, feedback: bool = False) -> int:
        """Create random synapses from every neuron in `source_index` to neurons in `dest_index`.
        Returns the number of edges created (edge count parity with Java).
        """
        if source_index < 0 or source_index >= len(self.layers):
            raise IndexError(f"source_index out of range: {source_index}")
        if dest_index < 0 or dest_index >= len(self.layers):
            raise IndexError(f"dest_index out of range: {dest_index}")
        p = max(0.0, min(1.0, float(probability)))
        src_layer = self.layers[source_index]
        dst_layer = self.layers[dest_index]
        count = 0
        for a in src_layer.get_neurons():
            for b in dst_layer.get_neurons():
                if self.rng.random() <= p:
                    try:
                        a.connect(b, feedback=feedback)
                        count += 1
                    except Exception:
                        # If connect signature differs, attempt positional
                        a.connect(b)
                        count += 1
        return count

    def bind_input(self, port: str, layer_indices: List[int]) -> None:
        self.input_ports[port] = list(layer_indices)

    def bind_output(self, port: str, layer_indices: List[int]) -> None:
        self.output_ports[port] = list(layer_indices)

    # ---------------- pulses ----------------
    def pulse_inhibition(self, factor: float):
        # forward to RegionBus if present, otherwise try each layer bus
        if self.bus is not None:
            setf = getattr(self.bus, "set_inhibition_factor", None) or getattr(self.bus, "set_inhibition", None)
            if callable(setf):
                setf(factor)
                return
        for layer in self.layers:
            bus = getattr(layer, "get_bus", lambda: None)()
            if bus is None: 
                continue
            setf = getattr(bus, "set_inhibition_factor", None) or getattr(bus, "set_inhibition", None)
            if callable(setf):
                setf(factor)

    def pulse_modulation(self, factor: float):
        if self.bus is not None:
            setf = getattr(self.bus, "set_modulation_factor", None) or getattr(self.bus, "set_modulation", None)
            if callable(setf):
                setf(factor)
                return
        for layer in self.layers:
            bus = getattr(layer, "get_bus", lambda: None)()
            if bus is None: 
                continue
            setf = getattr(bus, "set_modulation_factor", None) or getattr(bus, "set_modulation", None)
            if callable(setf):
                setf(factor)

    # ---------------- ticks ----------------
    def tick(self, port: str, value: float) -> RegionMetrics:
        metrics = RegionMetrics()
        entry = self.input_ports.get(port, [])
        for layer_idx in entry:
            self.layers[layer_idx].forward(value)
            metrics.inc_delivered_events(1)

        # end-of-tick: per-layer decay and housekeeping
        for layer in self.layers:
            layer.end_tick()

        # aggregate structure metrics
        for layer in self.layers:
            for neuron in layer.get_neurons():
                # neuron API uses slots() and get_outgoing()
                slots = neuron.slots() if hasattr(neuron, "slots") else []
                metrics.add_slots(len(slots))
                outgoing = neuron.get_outgoing() if hasattr(neuron, "get_outgoing") else []
                metrics.add_synapses(len(outgoing))
        return metrics

    def tick_image(self, port: str, frame) -> RegionMetrics:
        metrics = RegionMetrics()
        entry = self.input_ports.get(port, [])
        for layer_idx in entry:
            layer = self.layers[layer_idx]
            # If the layer is shape-aware and exposes forward_image, use it; else fall back to scalar drive
            if hasattr(layer, "forward_image"):
                layer.forward_image(frame)
            else:
                layer.forward(frame)  # best-effort
            metrics.inc_delivered_events(1)
        for layer in self.layers:
            layer.end_tick()
        for layer in self.layers:
            for neuron in layer.get_neurons():
                slots = neuron.slots() if hasattr(neuron, "slots") else []
                metrics.add_slots(len(slots))
                outgoing = neuron.get_outgoing() if hasattr(neuron, "get_outgoing") else []
                metrics.add_synapses(len(outgoing))
        return metrics

    # ---------------- maintenance ----------------
    def prune(self, synapse_stale_window: int = 10000, synapse_min_strength: float = 0.05) -> 'Region.PruneSummary':
        ps = Region.PruneSummary()
        # If neurons expose prune_synapses(...), call it; otherwise, keep zeros.
        for layer in self.layers:
            for neuron in layer.get_neurons():
                fn = getattr(neuron, "prune_synapses", None) or getattr(neuron, "pruneSynapses", None)
                if callable(fn):
                    try:
                        ps.prunedSynapses += int(fn(synapse_stale_window, synapse_min_strength))
                    except Exception:
                        pass
        return ps

    # ---------------- accessors ----------------
    def get_name(self) -> str:
        return self.name

    def get_layers(self) -> List[object]:
        return self.layers

    def get_bus(self):
        return self.bus
