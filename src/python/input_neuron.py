from __future__ import annotations

from neuron import Neuron


class InputNeuron(Neuron):
    """
    Sensory neuron: single-slot behaviour by default via compute_slot_id = 0.
    """
    def __init__(self, name: str, gain: float = 1.0, epsilon_fire: float = 0.01) -> None:
        super().__init__(name)
        self.gain: float = gain
        self.epsilon_fire: float = epsilon_fire

    # Route all inputs to slot 0 (retina-like pixel)
    def compute_slot_id(self, input_value: float) -> int:
        return 0

    # Maintain unified on_output contract (no side effects here)
    def on_output(self, amplitude: float) -> None:
        pass

    def end_tick(self) -> None:
        pass
