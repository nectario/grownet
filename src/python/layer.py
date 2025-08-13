from bus import LateralBus
from typing import List
from neuron import ExcitatoryNeuron, InhibitoryNeuron, ModulatoryNeuron, LateralBus
from src.python.slot_policy import SlotPolicyConfig


class Layer:
    """Mixes neuron types; maintains a shared LateralBus."""

    def __init__(self, size_excit: int, size_inhib: int = 0, size_mod: int = 0):

        self.slot_policy = SlotPolicyConfig()
        self.bus = LateralBus()
        self.neurons: List = []

        self.neurons += [ExcitatoryNeuron(f"E{i}", self.bus) for i in range(size_excit)]
        self.neurons += [InhibitoryNeuron(f"I{i}", self.bus) for i in range(size_inhib)]
        self.neurons += [ModulatoryNeuron(f"M{i}", self.bus) for i in range(size_mod)]

    def forward(self, input_value: float):
        for n in self.neurons:
            n.on_input(input_value)
        self.bus.decay()   # reset bus signals each timestep
