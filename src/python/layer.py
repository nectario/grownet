import random
from neuron_excitatory import ExcitatoryNeuron
from neuron_inhibitory import InhibitoryNeuron
from neuron_modulatory import ModulatoryNeuron
from lateral_bus import LateralBus

class Layer:
    def __init__(self, excitatory_count, inhibitory_count, modulatory_count):
        self.bus = LateralBus()
        self.rng = random.Random(1234)
        self.neurons = []
        # default slot policy baked into Neuron base
        slot_limit = -1
        for i in range(int(excitatory_count)):
            n = ExcitatoryNeuron(f"E{i}")
            n.set_bus(self.bus)
            self.neurons.append(n)
        for i in range(int(inhibitory_count)):
            n = InhibitoryNeuron(f"I{i}")
            n.set_bus(self.bus)
            self.neurons.append(n)
        for i in range(int(modulatory_count)):
            n = ModulatoryNeuron(f"M{i}")
            n.set_bus(self.bus)
            self.neurons.append(n)

    def get_neurons(self):
        return self.neurons

    def get_bus(self):
        return self.bus

    # wiring
    def wire_random_feedforward(self, probability):
        for a in self.neurons:
            for b in self.neurons:
                if a is b:
                    continue
                if self.rng.random() < probability:
                    a.connect(b, feedback=False)

    def wire_random_feedback(self, probability):
        for a in self.neurons:
            for b in self.neurons:
                if a is b:
                    continue
                if self.rng.random() < probability:
                    a.connect(b, feedback=True)

    # main drive
    def forward(self, value):
        for n in self.neurons:
            fired = n.on_input(value)
            if fired:
                n.on_output(value)

    def propagate_from(self, source_index, value):
        # default: treat like uniform drive from external source
        self.forward(value)

    def end_tick(self):
        # decay the bus; give neurons a chance to do housekeeping
        for n in self.neurons:
            n.end_tick()
        self.bus.decay()
