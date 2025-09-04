
from input_neuron import InputNeuron
from layer import Layer

class InputLayerND(Layer):
    def __init__(self, shape, gain, epsilon_fire):
        Layer.__init__(self, 0, 0, 0)
        if shape is None or len(shape) == 0:
            raise ValueError("shape must have rank >= 1")
        self.shape = [int(dim) for dim in shape]
        size = 1
        for dim in self.shape:
            if dim <= 0:
                raise ValueError("shape dims must be > 0")
            size *= dim
        self.size = int(size)
        for index in range(self.size):
            neuron = InputNeuron(f"IN[{index}]", gain=gain, epsilon_fire=epsilon_fire)
            neuron.set_bus(self.get_bus())
            try:
                neuron.owner = self
            except Exception:
                pass
            self.get_neurons().append(neuron)

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
        for index in range(self.size):
            value = float(flat[index])
            fired = neurons[index].on_input(value)
            if fired:
                neurons[index].on_output(value)

    def propagate_from(self, source_index, value):
        pass
