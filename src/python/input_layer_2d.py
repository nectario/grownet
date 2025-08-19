from input_neuron import InputNeuron
from layer import Layer

class InputLayer2D(Layer):
    def __init__(self, height, width, gain, epsilon_fire):
        # create empty layer (no default neurons)
        self.bus = super().get_bus() if hasattr(self, "_bus") else None  # placeholder
        # we cannot call super().__init__ because it would create mixed neurons;
        # instead, initialize skeleton fields as in Layer
        Layer.__init__(self, 0, 0, 0)
        self._height = int(height)
        self._width = int(width)
        # fill grid with InputNeurons
        for y in range(self._height):
            for x in range(self._width):
                n = InputNeuron(f"IN[{y},{x}]", gain=gain, epsilon_fire=epsilon_fire)
                n.set_bus(self.get_bus())
                self.get_neurons().append(n)

    def index(self, y, x):
        return int(y) * self._width + int(x)

    def forward_image(self, frame_2d):
        # frame_2d: iterable of rows
        h = min(self._height, len(frame_2d))
        for y in range(h):
            row = frame_2d[y]
            w = min(self._width, len(row))
            for x in range(w):
                idx = self.index(y, x)
                self.get_neurons()[idx].on_input(row[x])

    def propagate_from(self, source_index, value):
        # Inputs are sinks; nothing to do.
        pass
