from typing import List
from region_bus import RegionBus
from input_neuron import InputNeuron

class InputLayer2D:
    def __init__(self, height: int, width: int, gain: float, epsilon_fire: float, bus: RegionBus) -> None:
        self._h = int(height)
        self._w = int(width)
        self._gain = float(gain)
        self._eps = float(epsilon_fire)
        self._bus = bus
        self._neurons: List[InputNeuron] = [InputNeuron(f"IN_{r}_{c}", bus) for r in range(self._h) for c in range(self._w)]

    def get_neurons(self) -> List[InputNeuron]:
        return self._neurons

    def forward(self, value: float) -> None:
        # broadcast scalar to all inputs
        for n in self._neurons:
            n.on_input(value)

    def forward_image(self, frame: List[List[float]]) -> None:
        # flatten row-major; clip to [h,w]
        for r in range(min(self._h, len(frame))):
            row = frame[r]
            for c in range(min(self._w, len(row))):
                v = float(row[c]) * self._gain
                if abs(v) >= self._eps:
                    self._neurons[r*self._w + c].on_input(v)

    def end_tick(self) -> None:
        self._bus.end_tick()
        for n in self._neurons:
            n.end_tick()
