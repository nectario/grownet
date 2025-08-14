# layer.mojo — keep it minimal; wiring helpers + forward

from bus                 import LateralBus
from neuron_excitatory   import ExcitatoryNeuron
from neuron_inhibitory   import InhibitoryNeuron
from neuron_modulatory   import ModulatoryNeuron

struct Layer:
    var bus:      LateralBus
    var neurons:  List[Neuron]

    fn init(excitatory_count: Int64, inhibitory_count: Int64, modulatory_count: Int64) -> None:
        self.bus = LateralBus()
        self.neurons = []
        for i in range(excitatory_count):
            self.neurons.append(ExcitatoryNeuron(neuron_id=f"E{i}", bus=self.bus))
        for i in range(inhibitory_count):
            self.neurons.append(InhibitoryNeuron(neuron_id=f"I{i}", bus=self.bus))
        for i in range(modulatory_count):
            self.neurons.append(ModulatoryNeuron(neuron_id=f"M{i}", bus=self.bus))

    fn forward(self, value: F64) -> None:
        for n in self.neurons:
            let _ = n.on_input(value)

    fn decay(self) -> None:
        self.bus.decay()
