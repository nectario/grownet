from output_neuron import OutputNeuron
from layer import Layer

class OutputLayer2D(Layer):
    """Shape-aware sink: output neurons expose a 2D frame snapshot per tick."""
    def __init__(self, height, width, smoothing):
        Layer.__init__(self, 0, 0, 0)
        self.height = int(height)
        self.width = int(width)
        self.frame = [[0.0 for _ in range(self.width)] for _ in range(self.height)]
        for row_idx in range(self.height):
            for col_idx in range(self.width):
                neuron = OutputNeuron(f"OUT[{row_idx},{col_idx}]", smoothing=smoothing)
                neuron.set_bus(self.get_bus())
                try:
                    neuron.owner = self
                except Exception:
                    pass
                self.get_neurons().append(neuron)

    def index(self, y, x):
        return int(y) * self.width + int(x)

    def propagate_from(self, source_index, value):
        if source_index < 0 or source_index >= len(self.get_neurons()):
            return
        neuron = self.get_neurons()[source_index]
        fired = neuron.on_input(value)
        if fired:
            neuron.on_output(value)

    def end_tick(self):
        # Update frame from each output neuron's last value, then decay
        for neuron_index, neuron in enumerate(self.get_neurons()):
            neuron.end_tick()
            row_idx = neuron_index // self.width
            col_idx = neuron_index % self.width
            self.frame[row_idx][col_idx] = neuron.get_output_value()
        self.get_bus().decay()

    def get_frame(self):
        return self.frame
