from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Sequence, Tuple

from layer import Layer
from bus import LateralBus


@dataclass
class RegionMetrics:
    delivered_events: int
    total_slots: int
    total_synapses: int


@dataclass
class PruneSummary:
    pruned_synapses: int
    pruned_edges: int = 0  # reserved for tract-level pruning if we add Tracts later


class Region:
    """
    Region = collection of Layers plus a region-wide bus.
    Provides one-tick driving (scalar or image) and maintenance (prune).
    """
    def __init__(self, name: str):
        self.name: str = name
        self.layers: List[Layer] = []
        self.bus: LateralBus = LateralBus()
        self._input_ports: Dict[str, List[int]] = {}
        self._output_ports: Dict[str, List[int]] = {}

    # ----- construction / wiring ------------------------------------------------

    def add_layer(
        self,
        excitatory_count: int,
        inhibitory_count: int,
        modulatory_count: int,
    ) -> int:
        layer = Layer(
            excitatory_count=excitatory_count,
            inhibitory_count=inhibitory_count,
            modulatory_count=modulatory_count,
        )
        self.layers.append(layer)
        return len(self.layers) - 1

    def connect_layers(self, source_index: int, dest_index: int, probability: float, feedback: bool = False) -> int:
        """Wire random edges from every neuron in layer[source] to layer[dest]. Returns edges created."""
        src = self.layers[source_index]
        dst = self.layers[dest_index]
        edges = 0
        for a in src.neurons:
            for b in dst.neurons:
                # simple Erdos–Renyi wiring (layer-local RNG)
                if src._rng.random() < probability:
                    a.connect(b, feedback=feedback)
                    edges += 1
        return edges

    def bind_input(self, port: str, layer_indices: Sequence[int]) -> None:
        self._input_ports[port] = list(layer_indices)

    def bind_output(self, port: str, layer_indices: Sequence[int]) -> None:
        self._output_ports[port] = list(layer_indices)

    # ----- ticking (scalar) -----------------------------------------------------

    def tick(self, port: str, value: float) -> RegionMetrics:
        """
        Drive all entry layers bound to `port` with a single scalar `value`,
        flush one step, and decay buses. Returns RegionMetrics.
        """
        # Phase A: push into entry layers
        for idx in self._input_ports.get(port, ()):
            self.layers[idx].forward(value)

        # Phase B: (no explicit tract queues in the Python ref impl; propagation happens immediately)

        # Decay
        for layer in self.layers:
            layer.bus.decay()
        self.bus.decay()

        # Light metrics
        total_slots = 0
        total_synapses = 0
        for layer in self.layers:
            for n in layer.neurons:
                total_slots += len(n.slots)
                total_synapses += len(n.outgoing)

        # delivered_events: we approximate here as number of neurons that fired this tick (EMA-based in weights)
        # If you want an exact count, we can expose a per-tick counter in LateralBus or Layer.
        delivered_events = total_synapses  # placeholder metric; refine later if needed

        return RegionMetrics(
            delivered_events=delivered_events,
            total_slots=total_slots,
            total_synapses=total_synapses,
        )

    # ----- tick for images (kept for your image_io_demo) ------------------------

    def tick_image(self, port: str, frame) -> RegionMetrics:
        """
        Drive a bound input layer with a 2D frame (NumPy ndarray).
        Requires that the corresponding input layer knows how to fan-out the frame.
        For simple demos we inject the average intensity as a scalar to all entry layers.
        """
        try:
            import numpy as np  # local import to keep core dependency-light
            value = float(np.asarray(frame, dtype=float).mean())
        except Exception:
            value = float(frame)  # fall back to scalar if not ndarray

        return self.tick(port, value)

    # ----- maintenance ----------------------------------------------------------

    def prune(
        self,
        synapse_stale_window: int = 10_000,
        synapse_min_strength: float = 0.05,
    ) -> PruneSummary:
        """
        Remove outgoing synapses that are both stale (not used for `stale_window` ticks)
        AND weak (weight.strength < min_strength). Keeps neurons and slots intact.
        Mirrors the C++ Region::prune behavior.  (Tract pruning reserved for later.)
        """
        current_step = self.bus.current_step
        pruned = 0
        for layer in self.layers:
            for neuron in layer.neurons:
                pruned += neuron.prune_synapses(
                    current_step=current_step,
                    stale_window=synapse_stale_window,
                    min_strength=synapse_min_strength,
                )
        return PruneSummary(pruned_synapses=pruned)
