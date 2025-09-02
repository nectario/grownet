import random
from neuron_excitatory import ExcitatoryNeuron
from neuron_inhibitory import InhibitoryNeuron
from neuron_modulatory import ModulatoryNeuron
from lateral_bus import LateralBus

class Layer:
    """Mixed E/I/M population with a shared lateral bus."""
    def __init__(self, excitatory_count, inhibitory_count, modulatory_count):
        self.bus = LateralBus()
        self.rng = random.Random(1234)
        self.neurons = []
        # default slot policy baked into Neuron base
        slot_limit = -1
        for idx in range(int(excitatory_count)):
            neuron = ExcitatoryNeuron(f"E{idx}")
            neuron.set_bus(self.bus)
            self.neurons.append(neuron)
        for idx in range(int(inhibitory_count)):
            neuron = InhibitoryNeuron(f"I{idx}")
            neuron.set_bus(self.bus)
            self.neurons.append(neuron)
        for idx in range(int(modulatory_count)):
            neuron = ModulatoryNeuron(f"M{idx}")
            neuron.set_bus(self.bus)
            self.neurons.append(neuron)

    def get_neurons(self):
        return self.neurons

    def get_bus(self):
        return self.bus

    # wiring
    def wire_random_feedforward(self, probability):
        for src_neuron in self.neurons:
            for dst_neuron in self.neurons:
                if src_neuron is dst_neuron:
                    continue
                if self.rng.random() < probability:
                    src_neuron.connect(dst_neuron, feedback=False)

    def wire_random_feedback(self, probability):
        for src_neuron in self.neurons:
            for dst_neuron in self.neurons:
                if src_neuron is dst_neuron:
                    continue
                if self.rng.random() < probability:
                    src_neuron.connect(dst_neuron, feedback=True)

    # main drive
    def forward(self, value):
        """Drive all neurons with a scalar for this tick."""
        for neuron in self.neurons:
            fired = neuron.on_input(value)
            if fired:
                neuron.on_output(value)

    def propagate_from(self, source_index, value):
        # default: treat like uniform drive from external source
        self.forward(value)

    def propagate_from_2d(self, source_index: int, value: float, height: int, width: int) -> None:
        """Destination-side hook for 2D-aware propagation.

        Computes (row,col) from source_index and calls each neuron's spatial
        on_input_2d if available/enabled, else falls back to scalar on_input.
        """
        try:
            row = int(source_index) // int(width)
            col = int(source_index) % int(width)
        except Exception:
            # if shape is invalid, fallback to scalar
            row, col = 0, 0
        for neuron in self.neurons:
            fired = False
            if hasattr(neuron, "on_input_2d"):
                try:
                    fired = neuron.on_input_2d(value, row, col)
                except Exception:
                    fired = neuron.on_input(value)
            else:
                fired = neuron.on_input(value)
            if fired:
                neuron.on_output(value)

    def end_tick(self):
        # Decay the bus; give neurons a chance to do housekeeping
        for neuron in self.neurons:
            neuron.end_tick()
        self.bus.decay()
