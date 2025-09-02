from neuron_excitatory import ExcitatoryNeuron
from neuron_inhibitory import InhibitoryNeuron
from neuron_modulatory import ModulatoryNeuron
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

    fn forward(mut self, value: Float64) -> list[Spike]:
        var spikes = []
        # Modulation factor read once per neuron evaluate.
        var mod_factor = self.bus.modulation_factor

        var idx = 0
        for neuron in self.neurons_inh:
            if neuron.on_input(value, mod_factor):
                # emit inhibition
                self.bus.set_inhibition_factor(0.7)
                neuron.on_output(value)
            idx += 1

        idx = 0
        for neuron in self.neurons_mod:
            if neuron.on_input(value, mod_factor):
                self.bus.set_modulation_factor(1.5)
                neuron.on_output(value)
            idx += 1

        # Excitatory last: they actually propagate.
        idx = 0
        for neuron in self.neurons_exc:
            if neuron.on_input(value, mod_factor):
                neuron.on_output(value)
                spikes.append(Spike(idx, value))
            idx += 1

        return spikes

    fn end_tick(mut self) -> None:
        self.bus.decay()
