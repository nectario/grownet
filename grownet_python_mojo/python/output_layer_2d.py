from typing import List
from region_bus import RegionBus
from output_neuron import OutputNeuron

class OutputLayer2D:
    def __init__(self, height: int, width: int, smoothing: float, bus: RegionBus) -> None:
        self._h = int(height)
        self._w = int(width)
        self._bus = bus
        self._neurons: List[OutputNeuron] = [OutputNeuron(f"OUT_{r}_{c}", bus, smoothing=smoothing) for r in range(self._h) for c in range(self._w)]

    def get_neurons(self) -> List[OutputNeuron]:
        return self._neurons

    def forward(self, value: float) -> None:
        for n in self._neurons:
            n.on_input(value)

    def end_tick(self) -> None:
        self._bus.end_tick()
        for n in self._neurons:
            n.end_tick()
