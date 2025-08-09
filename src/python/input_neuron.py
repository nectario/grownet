from neuron import Neuron
from weight import Weight

def clamp01(x: float) -> float:
    return 0.0 if x < 0.0 else 1.0 if x > 1.0 else x

class InputNeuron(Neuron):
    """Single-slot sensor neuron using the unified onInput/onOutput contract.
    - Slot 0 is the only gate.
    - S0 imprint: threshold starts just below first effective value so it fires once initially.
    - Keeps calling self.fire(...) on successful onInput so routing works as before.
    """
    def __init__(self, name: str, gain: float = 1.0, epsilon_fire: float = 0.01):
        super().__init__(name)
        self.gain = gain
        self.epsilon_fire = epsilon_fire
        self.slots.setdefault(0, Weight())

    def onInput(self, value: float) -> bool:
        stimulus = clamp01(value * self.gain)
        slot = self.slots[0]
        modulation = getattr(self, "bus", None).modulation_factor if hasattr(self, "bus") else 1.0
        inhibition = getattr(self, "bus", None).inhibition_factor if hasattr(self, "bus") else 1.0
        effective = clamp01(stimulus * modulation * inhibition)

        if not slot.first_seen:
            slot.threshold_value = max(0.0, effective * (1.0 - self.epsilon_fire))
            slot.first_seen = True

        slot.strength_value = effective
        fired = slot.update_threshold(effective)
        self.fired_last = fired
        self.last_input_value = effective
        if fired:
            # Keep routing semantics; if your Layer drives propagation, you can remove this.
            try:
                self.fire(effective)
            except Exception:
                pass
        return fired

    def onOutput(self, amplitude: float) -> None:
        # Input neurons don't write; hook reserved for logging/instrumentation.
        return
