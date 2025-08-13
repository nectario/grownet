from neuron import Neuron, NeuronType, LateralBus

fn make_input_neuron(bus: LateralBus) -> Neuron:
    return Neuron(NeuronType.INPUT, bus)
