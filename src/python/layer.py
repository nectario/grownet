class Layer:
    def __init__(self, size):
        self.neurons = [Neuron(f"N{i}") for i in range(size)]

    def forward(self, x):
        for n in self.neurons:
            n.onInput(x)
