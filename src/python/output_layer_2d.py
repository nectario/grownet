from output_neuron import OutputNeuron
from layer import Layer

class OutputLayer2D(Layer):
    def __init__(self, height, width, smoothing):
        Layer.__init__(self, 0, 0, 0)
        self.height = int(height)
        self.width = int(width)
        self.frame = [[0.0 for _ in range(self.width)] for _ in range(self.height)]
        for y in range(self.height):
            for x in range(self.width):
                n = OutputNeuron(f"OUT[{y},{x}]", smoothing=smoothing)
                n.set_bus(self.get_bus())
                self.get_neurons().append(n)

    def index(self, y, x):
        return int(y) * self.width + int(x)

    def propagate_from(self, source_index, value):
        if source_index < 0 or source_index >= len(self.get_neurons()):
            return
        n = self.get_neurons()[source_index]
        fired = n.on_input(value)
        if fired:
            n.on_output(value)

    def end_tick(self):
        # update frame from each output neuron's last value, then decay
        for idx, neuron in enumerate(self.get_neurons()):
            neuron.end_tick()
            y = idx // self.width
            x = idx % self.width
            self.frame[y][x] = neuron.get_output_value()
        self.get_bus().decay()

    def get_frame(self):
        return self.frame
