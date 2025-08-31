from neuron import Neuron

class InhibitoryNeuron(Neuron):
    def fire(self, input_value):
        # Emit inhibition into shared bus (if any) and do not propagate spikes downstream
        if self.get_bus() is not None:
            # reduce effective learning / activity downstream (interpretation)
            self.get_bus().set_inhibition(0.7)
        # still call hooks so tracts can observe spikes if desired
        for hook in self.fire_hooks:
            hook(self, input_value)
