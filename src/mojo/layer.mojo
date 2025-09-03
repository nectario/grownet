from neuron_excitatory import ExcitatoryNeuron
from neuron_inhibitory import InhibitoryNeuron
from neuron_modulatory import ModulatoryNeuron
from neuron import Neuron
from lateral_bus import LateralBus

struct Spike:
    var neuron_index: Int
    var amplitude: Float64

struct Layer:
    var neurons_exc: list[ExcitatoryNeuron]
    var neurons_inh: list[InhibitoryNeuron]
    var neurons_mod: list[ModulatoryNeuron]
    var bus: LateralBus

    fn init(mut self, excitatory_count: Int, inhibitory_count: Int, modulatory_count: Int) -> None:
        self.neurons_exc = []
        self.neurons_inh = []
        self.neurons_mod = []
        self.bus = LateralBus()
        var neuron_index = 0
        while neuron_index < excitatory_count:
            self.neurons_exc.append(ExcitatoryNeuron("E" + String(neuron_index)))
            neuron_index += 1
        neuron_index = 0
        while neuron_index < inhibitory_count:
            self.neurons_inh.append(InhibitoryNeuron("I" + String(neuron_index)))
            neuron_index += 1
        neuron_index = 0
        while neuron_index < modulatory_count:
            self.neurons_mod.append(ModulatoryNeuron("M" + String(neuron_index)))
            neuron_index += 1

        # Share the same bus across all neuron cores (Python parity)
        for e in self.neurons_exc: e.core.bus = self.bus
        for i in self.neurons_inh: i.core.bus = self.bus
        for m in self.neurons_mod: m.core.bus = self.bus

    fn get_neurons(self) -> list[Neuron]:
        var alln = []
        for n in self.neurons_inh: alln.append(n.core)
        for n in self.neurons_mod: alln.append(n.core)
        for n in self.neurons_exc: alln.append(n.core)
        return alln

    fn forward(mut self, value: Float64) -> None:
        # Inhibit/modulate classes can express pulses in on_output; execute in order
        for n in self.neurons_inh:
            if n.on_input(value): n.on_output(value)
        for n in self.neurons_mod:
            if n.on_input(value): n.on_output(value)
        for n in self.neurons_exc:
            if n.on_input(value): n.on_output(value)

    fn propagate_from(mut self, source_index: Int, value: Float64) -> None:
        # Default: treat like uniform drive from external source
        self.forward(value)

    fn propagate_from_2d(mut self, source_index: Int, value: Float64, height: Int, width: Int) -> None:
        # Compute (row,col) from flattened index and call spatial on_input if available
        var row = source_index / width
        var col = source_index % width
        for n in self.get_neurons():
            if n.on_input_2d(value, row, col): n.on_output(value)

    fn end_tick(mut self) -> None:
        self.bus.decay()
