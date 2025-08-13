# neuron_excitatory.mojo
from neuron import Neuron, EXCITATORY

struct ExcitatoryNeuron(Neuron):
    fn init(self, neuron_id: String, bus) -> None:
        self.neuron_id = neuron_id
        self.bus = bus
        self.type_tag = EXCITATORY
