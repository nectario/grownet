from typing import List
from region_bus import RegionBus
from neuron import Neuron, ExcitatoryNeuron, InhibitoryNeuron, ModulatoryNeuron

class Layer:
    def __init__(self, excitatory_count: int, inhibitory_count: int, modulatory_count: int, bus: RegionBus) -> None:
        self._bus = bus
        self._neurons: List[Neuron] = []
        for i in range(excitatory_count):
            self._neurons.append(ExcitatoryNeuron(f"E{i}", bus))
        for i in range(inhibitory_count):
            self._neurons.append(InhibitoryNeuron(f"I{i}", bus))
        for i in range(modulatory_count):
            self._neurons.append(ModulatoryNeuron(f"M{i}", bus))

    def get_neurons(self) -> List[Neuron]:
        return self._neurons

    def forward(self, value: float) -> None:
        for n in self._neurons:
            n.on_input(value)

    def end_tick(self) -> None:
        # bus maintenance + neuron maintenance
        self._bus.end_tick()
        for n in self._neurons:
            n.end_tick()
