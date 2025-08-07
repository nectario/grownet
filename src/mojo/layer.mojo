from std.array import Array
from neuron import ExcitatoryNeuron, InhibitoryNeuron, ModulatoryNeuron
from bus import LateralBus

struct Layer:
    var neurons: Array[Neuron] = Array()
    var bus:     LateralBus    = LateralBus()

    fn init(self, ex: Int64, inh: Int64, mod: Int64):
        for i in range(ex):
            self.neurons.push(
                ExcitatoryNeuron(neuron_id=f"E{i}", bus=self.bus)
            )
        for i in range(inh):
            self.neurons.push(
                InhibitoryNeuron(neuron_id=f"I{i}", bus=self.bus)
            )
        for i in range(mod):
            self.neurons.push(
                ModulatoryNeuron(neuron_id=f"M{i}", bus=self.bus)
            )

    fn forward(self, v: Float64):
        for n in self.neurons:
            n.on_input(v)
        self.bus.decay()
