from neuron import Neuron, NeuronType, LateralBus

fn make_modulatory(bus: LateralBus) -> Neuron:
    return Neuron(NeuronType.MODULATORY, bus)
