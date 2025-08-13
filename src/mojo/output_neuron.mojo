from neuron import Neuron, NeuronType, LateralBus

fn make_output_neuron(bus: LateralBus, smoothing: Float64 = 0.20) -> Neuron:
    return Neuron(NeuronType.OUTPUT, bus, smoothing)

# Optional camelCase bridge
fn on_output(mut n: Neuron, amplitude: Float64):
    n.on_output(amplitude)
