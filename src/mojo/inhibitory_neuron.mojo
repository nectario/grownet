from neuron import Neuron, NeuronType, LateralBus

fn make_inhibitory(bus: LateralBus) -> Neuron:
    return Neuron(NeuronType.INHIBITORY, bus)
