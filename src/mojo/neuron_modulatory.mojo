# neuron_modulatory.mojo
from neuron import Neuron, MODULATORY

struct ModulatoryNeuron(Neuron):
    fn init(self, neuron_id: String, bus) -> None:
        self.neuron_id = neuron_id
        self.bus = bus
        self.type_tag = MODULATORY

    fn fire(self, input_value: F64) -> None:
        # Emit neuromodulation pulse
        self.bus.set_modulation(1.5)
