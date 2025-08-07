struct Layer:
    neurons: Array[@owned Neuron*]

    fn forward(self, x: F64):
        for n in self.neurons:
            n.on_input(x)
