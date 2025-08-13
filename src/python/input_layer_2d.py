from __future__ import annotations

from typing import List, Dict
import numpy as np

from bus import LateralBus
from input_neuron import InputNeuron


class InputLayer2D:
    """Shape-aware sensory layer (e.g., grayscale image) using unified on_input/on_output."""

    def __init__(self, height: int, width: int, *, gain: float = 1.0, epsilon_fire: float = 0.01) -> None:
        self.height = height
        self.width = width
        self.bus = LateralBus()
        self.neurons: List[InputNeuron] = []
        for y in range(height):
            for x in range(width):
                n = InputNeuron(name=f"IN[{y},{x}]", gain=gain, epsilon_fire=epsilon_fire)
                n.bus = self.bus
                self.neurons.append(n)

        # Optional: a place where external code can track wiring from this layer.
        self.adjacency: Dict[int, list[int]] = {}

    def index(self, y: int, x: int) -> int:
        return y * self.width + x

    def forward_image(self, image: np.ndarray) -> int:
        """Drive the layer with a 2‑D numpy array in [0,1]. Returns # of spikes emitted."""
        assert image.shape == (self.height, self.width)
        fired_count = 0
        for y in range(self.height):
            for x in range(self.width):
                idx = self.index(y, x)
                value = float(image[y, x])
                fired = self.neurons[idx].on_input(value)
                if fired:
                    # no-op for InputNeuron but keeps the on_output contract consistent
                    self.neurons[idx].on_output(value)
                    fired_count += 1
        return fired_count

    # Optional symmetry with other layer types
    def end_tick(self) -> None:
        pass
