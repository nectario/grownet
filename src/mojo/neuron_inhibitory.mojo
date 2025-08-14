# neuron_inhibitory.mojo — pulse lateral inhibition on bus

from neuron import Neuron

struct InhibitoryNeuron(Neuron):
    fn fire(self, _value: F64) -> None:
        self.bus.inhibition_factor = 0.7   # tune later
