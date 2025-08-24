
from input_neuron import InputNeuron
from layer import Layer

class InputLayerND(Layer):
    def __init__(self, shape, gain, epsilon_fire):
        Layer.__init__(self, 0, 0, 0)
        if shape is None or len(shape) == 0:
            raise ValueError("shape must have rank >= 1")
        self.shape = [int(d) for d in shape]
        size = 1
        for d in self.shape:
            if d <= 0:
                raise ValueError("shape dims must be > 0")
            size *= d
        self.size = int(size)
        for i in range(self.size):
            n = InputNeuron(f"IN[{i}]")
            n.set_bus(self.get_bus())
            self.get_neurons().append(n)

    def has_shape(self, other_shape):
        if other_shape is None or len(other_shape) != len(self.shape):
            return False
        return all(int(a) == int(b) for a, b in zip(self.shape, other_shape))

    def forward_nd(self, flat, shape):
        if not self.has_shape(shape):
            raise ValueError("shape mismatch with bound InputLayerND")
        if flat is None or len(flat) != self.size:
            raise ValueError(f"flat length {len(flat) if flat is not None else -1} != expected {self.size}")
        neurons = self.get_neurons()
        for i in range(self.size):
            value = float(flat[i])
            fired = neurons[i].on_input(value)
            if fired:
                neurons[i].on_output(value)

    def propagate_from(self, source_index, value):
        pass
