# src/python/region.py
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Optional

from layer import Layer
from neuron import Neuron
from weight import Weight


class RegionBus:
    """Region-wide, one-tick signals (same spirit as LateralBus, but spanning layers)."""
    def __init__(self) -> None:
        self.inhibition_factor: float = 1.0   # 1.0 = no inhibition
        self.modulation_factor: float = 1.0   # scales learning rate
        self.current_step: int = 0

    def decay(self) -> None:
        """Advance one tick; reset transients."""
        self.inhibition_factor = 1.0
        self.modulation_factor = 1.0
        self.current_step += 1


@dataclass
class InterLayerEdge:
    """Directed edge managed by a Tract (source neuron is implicit by the dict key)."""
    target: Neuron
    weight: Weight = field(default_factory=Weight)
    is_feedback: bool = False
    last_step: int = 0


@dataclass
class QueuedEvent:
    """Deferred delivery of a scalar to a target neuron (Phase B)."""
    target: Neuron
    value: float


class Tract:
    """
    A bundle of inter-layer connections (white-matter-like). It registers fire-hooks on
    source neurons so cross-layer traffic is queued, then flushed by the Region in Phase B.
    """
    def __init__(self, source: Layer, dest: Layer, region_bus: RegionBus, is_feedback: bool = False) -> None:
        self.source = source
        self.dest = dest
        self.region_bus = region_bus
        self.is_feedback = is_feedback

        # edges[src_neuron] -> list[InterLayerEdge]
        self.edges: Dict[Neuron, List[InterLayerEdge]] = {}
        self.queue: List[QueuedEvent] = []
        self._hooked_sources: set[Neuron] = set()

    def wire_dense_random(self, probability: float) -> None:
        """Create edges with the given probability; avoid duplicates."""
        if probability <= 0.0:
            return

        for src in self.source.neurons:
            for dst in self.dest.neurons:
                if src is dst:
                    continue
                # flip a coin
                from random import random
                if random() >= probability:
                    continue

                # add edge
                edge = InterLayerEdge(target=dst, is_feedback=self.is_feedback)
                self.edges.setdefault(src, []).append(edge)

                # register a single hook per (tract, src)
                if src not in self._hooked_sources:
                    src.register_fire_hook(self._make_source_hook(src))
                    self._hooked_sources.add(src)

    def _make_source_hook(self, src: Neuron):
        """Returns a closure: when `src` fires, reinforce edges and enqueue deliveries."""
        def on_source_fire(input_value: float, source_neuron: Neuron) -> None:
            # Safety: only respond to the neuron we were created for
            if source_neuron is not src:
                return

            edges = self.edges.get(src, [])
            if not edges:
                return

            for edge in edges:
                # Local learning at the inter-layer edge
                edge.weight.reinforce(
                    modulation_factor=self.region_bus.modulation_factor,
                    inhibition_factor=self.region_bus.inhibition_factor
                )
                fired = edge.weight.update_threshold(input_value)
                if fired:
                    self.queue.append(QueuedEvent(edge.target, input_value))
                    edge.last_step = self.region_bus.current_step
        return on_source_fire

    def flush(self) -> int:
        """Deliver queued events once (Phase B). Returns number of delivered events."""
        delivered = 0
        if not self.queue:
            return delivered
        # pop all current events; new ones (from cascaded tracts) will arrive next tick
        pending, self.queue = self.queue, []
        for event in pending:
            event.target.on_input(event.value)
            delivered += 1
        return delivered

    def prune_edges(self, stale_window: int, min_strength: float) -> int:
        """Remove edges that are stale and weak. Returns number of pruned edges."""
        pruned = 0
        keep_map: Dict[Neuron, List[InterLayerEdge]] = {}
        for src, edges in self.edges.items():
            kept = []
            for edge in edges:
                is_stale = (self.region_bus.current_step - edge.last_step) > stale_window
                is_weak = edge.weight.strength_value < min_strength
                if is_stale and is_weak:
                    pruned += 1
                else:
                    kept.append(edge)
            if kept:
                keep_map[src] = kept
        self.edges = keep_map
        return pruned


class Region:
    """A named collection of layers and tracts with a two-phase tick schedule."""
    def __init__(self, name: str) -> None:
        self.name = name
        self.layers: List[Layer] = []
        self.tracts: List[Tract] = []
        self.bus = RegionBus()
        self.input_ports: Dict[str, List[int]] = {}
        self.output_ports: Dict[str, List[int]] = {}

    # ----- construction -----

    def add_layer(self, excitatory_count: int, inhibitory_count: int, modulatory_count: int) -> int:
        """Create a layer and return its index."""
        layer = Layer(excitatory_count, inhibitory_count, modulatory_count)
        self.layers.append(layer)
        return len(self.layers) - 1

    def connect_layers(self, source_index: int, dest_index: int,
                       probability: float, feedback: bool = False) -> Tract:
        """Create a tract and random edges between two layers."""
        source = self.layers[source_index]
        dest = self.layers[dest_index]
        tract = Tract(source, dest, self.bus, is_feedback=feedback)
        tract.wire_dense_random(probability)
        self.tracts.append(tract)
        return tract

    def bind_input(self, port: str, layer_indices: List[int]) -> None:
        self.input_ports[port] = list(layer_indices)

    def bind_output(self, port: str, layer_indices: List[int]) -> None:
        self.output_ports[port] = list(layer_indices)

    # ----- region control -----

    def pulse_inhibition(self, factor: float) -> None:
        self.bus.inhibition_factor = factor

    def pulse_modulation(self, factor: float) -> None:
        self.bus.modulation_factor = factor

    # ----- main loop -----

    def tick(self, port: str, value: float) -> Dict[str, float]:
        """
        Two-phase update:
          Phase A: deliver external input to entry layers (intra-layer propagation happens).
          Phase B: flush inter-layer tracts once.
          Decay:   reset buses and advance step.
        Returns a small metrics dict.
        """
        # Phase A: external input
        for idx in self.input_ports.get(port, []):
            self.layers[idx].forward(value)

        # Phase B: inter-layer propagation
        delivered = 0
        for tract in self.tracts:
            delivered += tract.flush()

        # Decay
        for layer in self.layers:
            layer.bus.decay()
        self.bus.decay()

        # Light metrics
        total_slots = sum(len(n.slots) for layer in self.layers for n in layer.neurons)
        total_synapses = sum(len(n.outgoing) for layer in self.layers for n in layer.neurons)
        return {
            "delivered_events": float(delivered),
            "total_slots": float(total_slots),
            "total_synapses": float(total_synapses),
        }

    # ----- maintenance -----

    def prune(self, synapse_stale_window: int = 10_000, synapse_min_strength: float = 0.05,
              tract_stale_window: int = 10_000, tract_min_strength: float = 0.05) -> Dict[str, int]:
        """Prune weak/stale synapses in layers and edges in tracts. Returns counts."""
        # per-neuron synapses
        pruned_syn = 0
        for layer in self.layers:
            for neuron in layer.neurons:
                before = len(neuron.outgoing)
                neuron.prune_synapses(self.bus.current_step, synapse_stale_window, synapse_min_strength)
                pruned_syn += before - len(neuron.outgoing)
        # tract edges
        pruned_edges = sum(t.prune_edges(tract_stale_window, tract_min_strength) for t in self.tracts)
        return {"pruned_synapses": pruned_syn, "pruned_edges": pruned_edges}


def set_slot_policy(self, policy):
    # Set on all layers (simple broadcast)
    for layer in self.layers:
        if hasattr(layer, "slot_policy"):
            layer.slot_policy = policy
