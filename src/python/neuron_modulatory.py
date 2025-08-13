from .neuron import Neuron

class ModulatoryNeuron(Neuron):
    def fire(self, input_value: float) -> None:
        # Boost learning this tick
        self.bus.pulse_modulation(1.5)
        for hook in self.fire_hooks:
            hook(input_value, self)
