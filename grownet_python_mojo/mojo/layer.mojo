from region_bus import RegionBus
from neuron import Neuron
import Vector

class Layer:
    var bus: RegionBus
    var neurons: Vector[Neuron]

    fn __init__(inout self, excitatory_count: Int64, inhibitory_count: Int64, modulatory_count: Int64, bus: RegionBus):
        self.bus = bus
        self.neurons = Vector[Neuron]()
        # For now, make all generic "Neuron" instances; specialization can be added later.
        var i: Int64 = 0
        while i < excitatory_count:
            self.neurons.push_back(Neuron("E" + str(i), bus))
            i += 1
        i = 0
        while i < inhibitory_count:
            self.neurons.push_back(Neuron("I" + str(i), bus))
            i += 1
        i = 0
        while i < modulatory_count:
            self.neurons.push_back(Neuron("M" + str(i), bus))
            i += 1

    fn get_neurons(self) -> Vector[Neuron]:
        return self.neurons

    fn forward(inout self, value: Float64):
        for n in self.neurons:
            n.on_input(value)

    fn end_tick(inout self):
        self.bus.end_tick()
        for n in self.neurons:
            n.end_tick()
