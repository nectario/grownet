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

    fn init(inout self, excitatory_count: Int, inhibitory_count: Int, modulatory_count: Int) -> None:
        self.neurons_exc = []
        self.neurons_inh = []
        self.neurons_mod = []
        self.bus = LateralBus()
        var i = 0
        while i < excitatory_count:
            self.neurons_exc.append(ExcitatoryNeuron("E" + String(i)))
            i += 1
        i = 0
        while i < inhibitory_count:
            self.neurons_inh.append(InhibitoryNeuron("I" + String(i)))
            i += 1
        i = 0
        while i < modulatory_count:
            self.neurons_mod.append(ModulatoryNeuron("M" + String(i)))
            i += 1

    fn forward(inout self, value: Float64) -> list[Spike]:
        var spikes = []
        # Modulation factor read once per neuron evaluate.
        let mod_factor = self.bus.modulation_factor

        var idx = 0
        for n in self.neurons_inh:
            if n.on_input(value, mod_factor):
                # emit inhibition
                self.bus.set_inhibition_factor(0.7)
                n.on_output(value)
            idx += 1

        idx = 0
        for n in self.neurons_mod:
            if n.on_input(value, mod_factor):
                self.bus.set_modulation_factor(1.5)
                n.on_output(value)
            idx += 1

        # Excitatory last: they actually propagate.
        idx = 0
        for n in self.neurons_exc:
            if n.on_input(value, mod_factor):
                n.on_output(value)
                spikes.append(Spike(idx, value))
            idx += 1

        return spikes

    fn end_tick(inout self) -> None:
        self.bus.decay()
