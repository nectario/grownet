from dataclasses import dataclass, field
from typing import List
import random

from .synapse import Synapse
from .layer import Layer

@dataclass
class Tract:
    source: Layer
    target: Layer
    is_feedback: bool = False
    edges: List[Synapse] = field(default_factory=list)

    def wire_dense_random(self, probability: float) -> None:
        self.edges.clear()
        for source_neuron in self.source.neurons:
            for target_neuron in self.target.neurons:
                if random.random() < probability:
                    syn = source_neuron.connect(target_neuron, is_feedback=self.is_feedback)
                    self.edges.append(syn)

    def flush(self) -> int:
        # In this simplified version, intra-layer propagation happens immediately in Layer.forward.
        # A 'flush' here would route any queued inter-layer events if we add queuing later.
        return 0

    def prune_edges(self, min_strength: float = 0.05) -> int:
        before = len(self.edges)
        self.edges = [e for e in self.edges if e.weight.strength >= min_strength]
        return before - len(self.edges)
