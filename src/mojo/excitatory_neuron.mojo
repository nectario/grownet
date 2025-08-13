from neuron import Neuron, NeuronType, LateralBus

fn make_excitatory(bus: LateralBus) -> Neuron:
    return Neuron(NeuronType.EXCITATORY, bus)
