from typing import List
import numpy as np
from input_neuron import InputNeuron
from layer import LateralBus

class InputLayer2D:
    """Shape-aware sensory layer (e.g., grayscale image) using unified onInput/onOutput."""
    def __init__(self, height: int, width: int, gain: float = 1.0, epsilon_fire: float = 0.01):
        self.height = height
        self.width = width
        self.bus = LateralBus()
        self.neurons: List[InputNeuron] = []
        for y in range(height):
            for x in range(width):
                n = InputNeuron(name=f"IN[{y},{x}]", gain=gain, epsilon_fire=epsilon_fire)
                n.bus = self.bus
                self.neurons.append(n)
        self.adjacency = {}

    def index(self, y: int, x: int) -> int:
        return y * self.width + x

    def forward_image(self, image: np.ndarray) -> None:
        assert image.shape == (self.height, self.width)
        for y in range(self.height):
            for x in range(self.width):
                idx = self.index(y, x)
                value = float(image[y, x])
                fired = self.neurons[idx].onInput(value)
                if fired:
                    self.neurons[idx].onOutput(value)  # no-op but keeps the contract
