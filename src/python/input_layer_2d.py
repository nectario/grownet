from input_neuron import InputNeuron
from layer import Layer

class InputLayer2D(Layer):
    """Shape-aware entry layer: one InputNeuron per pixel."""
    def __init__(self, height, width, gain, epsilon_fire):

        # create empty layer (no default neurons)
        self.bus = super().get_bus() if hasattr(self, "bus") else None  # placeholder

        # we cannot call super().__init__ because it would create mixed neurons;
        # instead, initialize skeleton fields as in Layer

        Layer.__init__(self, 0, 0, 0)

        self.height = int(height)
        self.width = int(width)

        # fill grid with InputNeurons
        for row_idx in range(self.height):
            for col_idx in range(self.width):
                neuron = InputNeuron(f"IN[{row_idx},{col_idx}]", gain=gain, epsilon_fire=epsilon_fire)
                neuron.set_bus(self.get_bus())
                try:
                    neuron.owner = self
                except Exception:
                    pass
                self.get_neurons().append(neuron)

    def index(self, y, x):
        return int(y) * self.width + int(x)

    def forward_image(self, frame_2d):

        """Deliver a 2D frame (row-major) to matching input neurons."""
        height_limit = min(self.height, len(frame_2d))
        for row_idx in range(height_limit):
            row = frame_2d[row_idx]
            width_limit = min(self.width, len(row))
            for col_idx in range(width_limit):
                neuron_index = self.index(row_idx, col_idx)
                self.get_neurons()[neuron_index].on_input(row[col_idx])

    def propagate_from(self, source_index, value):
        # Inputs are sinks; nothing to do.
        pass
