# layer.mojo
from bus import LateralBus
from neuron_excitatory import ExcitatoryNeuron
from neuron_inhibitory import InhibitoryNeuron
from neuron_modulatory import ModulatoryNeuron

struct Layer:
    var bus: LateralBus
    var neurons = []  # list of Neuron

    fn init(self, excitatory_count: Int64, inhibitory_count: Int64, modulatory_count: Int64) -> None:
        self.bus = LateralBus()
        # Create neurons
        for i in range(excitatory_count):
            self.neurons.append(ExcitatoryNeuron(f"E{i}", self.bus))
        for i in range(inhibitory_count):
            self.neurons.append(InhibitoryNeuron(f"I{i}", self.bus))
        for i in range(modulatory_count):
            self.neurons.append(ModulatoryNeuron(f"M{i}", self.bus))

    fn forward(self, input_value: F64) -> None:
        for n in self.neurons:
            n.on_input(input_value)
        self.bus.decay()
