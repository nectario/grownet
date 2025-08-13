from .neuron import Neuron

class InhibitoryNeuron(Neuron):
    def fire(self, input_value: float) -> None:
        # Lateral inhibition pulse (e.g., cut learning strength this tick)
        self.bus.pulse_inhibition(0.7)  # keep simple for now
        # still run hooks for observability
        for hook in self.fire_hooks:
            hook(input_value, self)
