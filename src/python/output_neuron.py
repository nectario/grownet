from neuron import Neuron
from weight import Weight

class OutputNeuron(Neuron):
    """Single-slot actuator neuron using the unified onInput/onOutput contract.
    - onInput: gate + reinforcement (does NOT fire/propagate)
    - onOutput: accumulate contributions for this tick
    - end_tick(): finalize with EMA smoothing (implemented on the layer or here)
    """
    def __init__(self, name: str, smoothing: float = 0.2):
        super().__init__(name)
        self.slots.setdefault(0, Weight())
        self.smoothing = smoothing
        self.accumulated_sum = 0.0
        self.accumulated_count = 0
        self.output_value = 0.0

    def onInput(self, value: float) -> bool:
        slot = self.slots[0]
        modulation = getattr(self, "bus", None).modulation_factor if hasattr(self, "bus") else 1.0
        inhibition = getattr(self, "bus", None).inhibition_factor if hasattr(self, "bus") else 1.0
        slot.reinforce(modulation, inhibition)
        fired = slot.update_threshold(value)
        self.fired_last = fired
        self.last_input_value = value
        return fired

    def onOutput(self, amplitude: float) -> None:
        self.accumulated_sum += amplitude
        self.accumulated_count += 1

    def end_tick(self) -> None:
        if self.accumulated_count > 0:
            mean = self.accumulated_sum / self.accumulated_count
            self.output_value = (1.0 - self.smoothing) * self.output_value + self.smoothing * mean
        self.accumulated_sum = 0.0
        self.accumulated_count = 0
