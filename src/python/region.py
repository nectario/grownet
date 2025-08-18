# region.py
# Region orchestration updated to use RegionMetrics helpers.
# This module assumes classes Layer, InputLayer2D are available in the same directory.
from typing import List, Dict
from metrics import RegionMetrics

# Forward imports are intentionally light to avoid tight coupling;
# Region only relies on the public surface of Layer and InputLayer2D.
# - Layer must provide: forward(value: float) -> None, endTick() -> None, getNeurons() -> List[Neuron]
# - InputLayer2D must provide: forwardImage(frame) -> None

class Region:
    class PruneSummary:
        def __init__(self):
            self.pruned_synapses = 0
            self.pruned_edges = 0  # reserved

    def __init__(self, name: str):
        self.name: str = name
        self.layers: List[object] = []
        self.input_ports: Dict[str, List[int]] = {}
        self.output_ports: Dict[str, List[int]] = {}
        # RegionBus reserved; keep parity with Java/C++
        self._bus = None

    # ---------- construction: add layers (shape-aware helpers are optional in Python layer) ----------
    def add_layer(self, excitatoryCount: int, inhibitoryCount: int, modulatoryCount: int) -> int:
        # Defer to a Layer factory expected to exist; user keeps their current Layer API.
        from layer import Layer  # local import to prevent circular deps during tooling
        layer = Layer(excitatoryCount, inhibitoryCount, modulatoryCount)
        self.layers.append(layer)
        return len(self.layers) - 1

    def add_input_ayer_2d(self, height: int, width: int, gain: float, epsilonFire: float) -> int:
        from input_layer_2d import InputLayer2D
        layer = InputLayer2D(height, width, gain, epsilonFire)
        self.layers.append(layer)
        return len(self.layers) - 1

    def add_output_layer_2d(self, height: int, width: int, smoothing: float) -> int:
        from output_layer_2d import OutputLayer2D
        layer = OutputLayer2D(height, width, smoothing)
        self.layers.append(layer)
        return len(self.layers) - 1

    # ---------- wiring (kept as simple pass-throughs to Layer helpers or manual connects in user code) ----------
    def bind_input(self, port: str, layerIndices: List[int]) -> None:
        self.input_ports[port] = list(layerIndices)

    def bind_output(self, port: str, layerIndices: List[int]) -> None:
        self.output_ports[port] = list(layerIndices)

    # ---------- tick (scalar) ----------
    def tick(self, port: str, value: float) -> RegionMetrics:
        from layer import Layer
        region_metrics = RegionMetrics()
        entry = self.input_ports.get(port)
        if entry is not None:
            for idx in entry:
                self.layers[idx].forward(value)
                region_metrics.inc_delivered_events()
        # end-of-tick housekeeping
        for layer in self.layers:
            layer.end_tick()
        # aggregates
        for layer in self.layers:
            for neuron in layer.get_neurons():
                # Neuron expected to provide getSlots() and getOutgoing()
                region_metrics.add_slots(len(neuron.getSlots()))
                region_metrics.add_synapses(len(neuron.getOutgoing()))
        return region_metrics

    # ---------- tick (image) ----------
    def tick_image(self, port: str, frame) -> RegionMetrics:
        from layer import Layer
        region_metrics = RegionMetrics()
        entry = self.input_ports.get(port)
        if entry is not None:
            for idx in entry:
                layer = self.layers[idx]
                # Only drive shape-aware input layers
                # Import type here to avoid import cycles when the user packages the project.
                try:
                    from input_layer_2d import InputLayer2D
                    if isinstance(layer, InputLayer2D):
                        layer.forward_image(frame)
                        region_metrics.inc_delivered_events()
                except Exception:
                    # If InputLayer2D is not present in this environment, ignore.
                    pass
        # end-of-tick housekeeping
        for layer in self.layers:
            layer.end_tick()
        # aggregates
        for layer in self.layers:
            for neuron in layer.get_neurons():
                region_metrics.add_slots(len(neuron.get_slots()))
                region_metrics.add_synapses(len(neuron.get_outgoing()))
        return region_metrics

    # ---------- maintenance ----------
    def prune(self, synapseStaleWindow: int, synapseMinStrength: float) -> 'Region.PruneSummary':
        from layer import Layer
        ps = Region.PruneSummary()
        for layer in self.layers:
            for neuron in layer.get_neurons():
                # Expect Neuron.pruneSynapses to exist and return an int
                ps.pruned_synapses += int(neuron.pruneSynapses(synapseStaleWindow, synapseMinStrength))
        return ps

    # ---------- accessors ----------
    def get_name(self) -> str:
        return self.name

    def get_layers(self) -> List[object]:
        return self.layers

    def get_bus(self):
        return self._bus
