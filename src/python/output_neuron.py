from __future__ import annotations
from neuron import Neuron
from weight import Weight

class OutputNeuron(Neuron):
    """Single-slot writer neuron (slot 0 only)."""
    def __init__(self, name: str, smoothing: float = 0.2):
        super().__init__(name)
        self.slots.setdefault(0, Weight())
        self.smoothing = smoothing
        self.accumulated_sum = 0.0
        self.accumulated_count = 0
        self.output_value = 0.0

    def on_routed_event(self, value: float) -> bool:
        slot = self.slots[0]
        modulation = getattr(self, "bus", None).modulation_factor if hasattr(self, "bus") else 1.0
        inhibition = getattr(self, "bus", None).inhibition_factor if hasattr(self, "bus") else 1.0
        slot.reinforce(modulation, inhibition)
        fired = slot.update_threshold(value)

        self.fired_last = fired
        self.last_input_value = value
        if fired:
            self.accumulated_sum += value
            self.accumulated_count += 1
        return fired

    def end_tick(self) -> None:
        if self.accumulated_count > 0:
            mean = self.accumulated_sum / self.accumulated_count
            self.output_value = (1.0 - self.smoothing) * self.output_value + self.smoothing * mean
        self.accumulated_sum = 0.0
        self.accumulated_count = 0
