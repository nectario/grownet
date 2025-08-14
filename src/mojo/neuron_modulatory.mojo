# neuron_modulatory.mojo — pulse neuromodulation on bus

from neuron import Neuron

struct ModulatoryNeuron(Neuron):
    fn fire(self, _value: F64) -> None:
        self.bus.modulation_factor = 1.5   # tune later
