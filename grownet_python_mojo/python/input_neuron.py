from neuron import Neuron

class InputNeuron(Neuron):
    def on_input(self, value: float) -> bool:
        # For input neurons we just pass the value through.
        return self.fire(value)
