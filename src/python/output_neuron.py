from __future__ import annotations

from neuron import Neuron


class OutputNeuron(Neuron):
    """
    Motor/actuator neuron: single-slot; exposes smoothed `output_value`.
    `on_output(amplitude)` records a pending value; `end_tick()` applies smoothing.
    """
    def __init__(self, name: str, smoothing: float = 0.2) -> None:
        super().__init__(name)
        self.smoothing: float = float(smoothing)
        self.output_value: float = 0.0
        self._pending_output: float = 0.0

    def compute_slot_id(self, input_value: float) -> int:
        return 0

    def on_output(self, amplitude: float) -> None:
        self._pending_output = float(amplitude)

    def end_tick(self) -> None:
        alpha = self.smoothing
        self.output_value = (1.0 - alpha) * self.output_value + alpha * self._pending_output
        # carry over last amplitude unless overwritten on the next tick
