# region.py — Python Region implementation (clean, parity-focused)
from typing import List, Dict, Any
import random
from metrics import RegionMetrics
from typing import List, Dict, Any, Callable, SupportsInt, cast

# Layer and shape-aware layers are imported lazily to avoid import cycles.


class Region:
    class PruneSummary:
        def __init__(self):
            self.prunedSynapses = 0
            self.prunedEdges = 0  # reserved

    def __init__(self, name: str):
        self.name: str = name
        self.layers: List[Any] = []          # Any to keep static analyzers calm
        self.input_ports: Dict[str, List[int]] = {}
        self.output_ports: Dict[str, List[int]] = {}
        # Edge layers per port (created lazily on bind)
        self.input_edges: Dict[str, int] = {}
        self.output_edges: Dict[str, int] = {}
        # Region-scope bus (optional; some codebases keep only per-layer buses)
        self.bus = None
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
        Returns the number of edges created (edge count parity with Java/C++)."""
        if source_index < 0 or source_index >= len(self.layers):
            raise IndexError(f"source_index out of range: {source_index}")
        if dest_index < 0 or dest_index >= len(self.layers):
            raise IndexError(f"dest_index out of range: {dest_index}")
        p = max(0.0, min(1.0, float(probability)))
        src_layer = self.layers[source_index]
        dst_layer = self.layers[dest_index]
        count = 0
        # Layer exposes get_neurons(); neurons expose connect(target, feedback=False)
        for a in getattr(src_layer, "get_neurons")():
            for b in getattr(dst_layer, "get_neurons")():
                if self.rng.random() <= p:
                    try:
                        a.connect(b, feedback=feedback)
                    except TypeError:
                        a.connect(b)
                    count += 1
        return count

    # ---------------- edge helpers ----------------
    def ensure_input_edge(self, port: str) -> int:
        """Ensure an Input edge layer exists for this port; create lazily."""
        idx = self.input_edges.get(port)
        if idx is not None:
            return idx
        # Minimal scalar input edge: a 1-neuron layer that forwards to internal graph.
        edge_idx = self.add_layer(1, 0, 0)
        self.input_edges[port] = edge_idx
        return edge_idx

    def ensure_output_edge(self, port: str) -> int:
        """Ensure an Output edge layer exists for this port; create lazily."""
        idx = self.output_edges.get(port)
        if idx is not None:
            return idx
        # Minimal scalar output edge: a 1-neuron layer acting as a sink.
        edge_idx = self.add_layer(1, 0, 0)
        self.output_edges[port] = edge_idx
        return edge_idx

    def bind_input(self, port: str, layer_indices: List[int]) -> None:
        self.input_ports[port] = list(layer_indices)
        in_edge = self.ensure_input_edge(port)
        for li in layer_indices:
            self.connect_layers(in_edge, li, 1.0, False)

    def bind_input_2d(self, port: str, height: int, width: int, gain: float, epsilon_fire: float, attach_layers: List[int]) -> None:
        from input_layer_2d import InputLayer2D
        # create or reuse edge
        edge_idx = self.input_edges.get(port)
        if edge_idx is None or not isinstance(self.layers[edge_idx], InputLayer2D):
            edge_idx = self.add_input_layer_2d(height, width, gain, epsilon_fire)
            self.input_edges[port] = edge_idx
        # wire edge → attached layers
        for layer_index in attach_layers:
            self.connect_layers(edge_idx, layer_index, 1.0, False)


    def bind_output(self, port: str, layer_indices: List[int]) -> None:
        self.output_ports[port] = list(layer_indices)
        out_edge = self.ensure_output_edge(port)
        for li in layer_indices:
            self.connect_layers(li, out_edge, 1.0, False)

    # ---------------- pulses ----------------
    def pulse_inhibition(self, factor: float) -> None:
        """Raise inhibition for the next tick (ephemeral)."""
        try:
            if self.bus is not None and hasattr(self.bus, "inhibition_factor"):
                self.bus.inhibition_factor = factor
        except Exception:
            pass
        for layer in self.layers:
            try:
                if hasattr(layer, "bus") and layer.bus is not None:
                    layer.bus.inhibition_factor = factor
            except Exception:
                pass

    def pulse_modulation(self, factor: float) -> None:
        """Scale modulation for the next tick (ephemeral)."""
        try:
            if self.bus is not None and hasattr(self.bus, "modulation_factor"):
                self.bus.modulation_factor = factor
        except Exception:
            pass
        for layer in self.layers:
            try:
                if hasattr(layer, "bus") and layer.bus is not None:
                    layer.bus.modulation_factor = factor
            except Exception:
                pass

    # ---------------- ticks ----------------
    def tick(self, port: str, value: float) -> RegionMetrics:
        metrics = RegionMetrics()

        edge_idx = self.input_edges.get(port)
        if edge_idx is None:
            raise KeyError(f"No InputEdge for port '{port}'. Call bind_input(...) first.")

        self.layers[edge_idx].forward(value)
        metrics.inc_delivered_events(1)

        for layer in self.layers:
            layer.end_tick()

        if self.bus is not None and hasattr(self.bus, "decay"):
            self.bus.decay()

        for layer in self.layers:
            for neuron in getattr(layer, "get_neurons")():
                slots = neuron.slots() if hasattr(neuron, "slots") else []
                metrics.add_slots(len(slots))
                outgoing = neuron.get_outgoing() if hasattr(neuron, "get_outgoing") else []
                metrics.add_synapses(len(outgoing))

        return metrics


    def tick_image(self, port: str, frame) -> RegionMetrics:
        metrics = RegionMetrics()

        edge_idx = self.input_edges.get(port)
        if edge_idx is None:
            raise KeyError(f"No InputEdge for port '{port}'. Bind a 2D input edge before tick_image().")

        layer = self.layers[edge_idx]
        if not hasattr(layer, "forward_image"):
            raise TypeError(f"InputEdge for '{port}' is not 2D. Use an InputLayer2D edge.")

        layer.forward_image(frame)
        metrics.inc_delivered_events(1)

        for layer in self.layers:
            layer.end_tick()
        if self.bus is not None and hasattr(self.bus, "decay"):
            self.bus.decay()

        for layer in self.layers:
            for neuron in getattr(layer, "get_neurons")():
                slots = neuron.slots() if hasattr(neuron, "slots") else []
                metrics.add_slots(len(slots))
                outgoing = neuron.get_outgoing() if hasattr(neuron, "get_outgoing") else []
                metrics.add_synapses(len(outgoing))
        return metrics

    # ---------------- maintenance ----------------
    def prune(
        self,
        synapse_stale_window: int = 10000,
        synapse_min_strength: float = 0.05) -> 'Region.PruneSummary':

        ps = Region.PruneSummary()

        # A prune function takes (int, float) and returns something int()-convertible.
        PruneFn = Callable[[int, float], SupportsInt]

        for layer in self.layers:
            for neuron in getattr(layer, "get_neurons")():
                fn = getattr(neuron, "prune_synapses", None) or getattr(neuron, "pruneSynapses", None)
                if callable(fn):
                    prune_fn = cast(PruneFn, fn)
                    try:
                        result = prune_fn(synapse_stale_window, synapse_min_strength)
                    except Exception:
                        result = 0  # defensive default if an impl raises
                    try:
                        ps.prunedSynapses += int(result)
                    except (TypeError, ValueError):
                        # If an implementation returns a non-numeric/None, ignore it.
                        pass
        return ps

    # ---------------- accessors ----------------
    def get_name(self) -> str:
        return self.name

    def get_layers(self) -> List[Any]:
        return self.layers

    def get_bus(self):
        return self.bus
