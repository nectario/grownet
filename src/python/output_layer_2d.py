from typing import List
import numpy as np
from output_neuron import OutputNeuron
from layer import LateralBus

class OutputLayer2D:
    """Shape-aware output layer (e.g., image writer) using unified onInput/onOutput."""
    def __init__(self, height: int, width: int, smoothing: float = 0.2):
        self.height = height
        self.width = width
        self.bus = LateralBus()
        self.neurons: List[OutputNeuron] = []
        for y in range(height):
            for x in range(width):
                n = OutputNeuron(name=f"OUT[{y},{x}]", smoothing=smoothing)
                n.bus = self.bus
                self.neurons.append(n)
        self.frame = np.zeros((height, width), dtype=float)

    def index(self, y: int, x: int) -> int:
        return y * self.width + x

    def propagate_from(self, source_index: int, value: float) -> None:
        if 0 <= source_index < len(self.neurons):
            n = self.neurons[source_index]
            fired = n.onInput(value)
            if fired:
                n.onOutput(value)

    def end_tick(self) -> None:
        for idx, neuron in enumerate(self.neurons):
            neuron.end_tick()
            y, x = divmod(idx, self.width)
            self.frame[y, x] = neuron.output_value

    def get_frame(self) -> np.ndarray:
        return self.frame.copy()
