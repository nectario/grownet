# neuron_excitatory.mojo — default spike = “forward”

from neuron import Neuron

struct ExcitatoryNeuron(Neuron):
    fn fire(self, input_value: F64) -> None:
        # For now, fan-out wiring lives in Layer/Region.
        # Keep the place-holder hook for consistency.
        pass
