# neuron_inhibitory.mojo
from neuron import Neuron, INHIBITORY

struct InhibitoryNeuron(Neuron):
    fn init(self, neuron_id: String, bus) -> None:
        self.neuron_id = neuron_id
        self.bus = bus
        self.type_tag = INHIBITORY

    fn fire(self, input_value: F64) -> None:
        # Emit lateral inhibition pulse
        self.bus.set_inhibition(0.7)
