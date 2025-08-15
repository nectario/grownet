from neuron_base import Neuron

class ModulatoryNeuron(Neuron):
    def fire(self, input_value):
        if self.get_bus() is not None:
            # increase learning rate momentarily
            self.get_bus().set_modulation_factor(1.5)
        for hook in getattr(self, "_fire_hooks", []):
            hook(self, input_value)
