from neuron import Neuron

struct ExcitatoryNeuron:
    var core: Neuron

    fn init(inout self, neuron_id: String, slot_limit: Int = -1) -> None:
        self.core = Neuron(neuron_id, slot_limit)

    fn on_input(inout self, value: Float64, modulation_factor: Float64) -> Bool:
        return self.core.on_input(value, modulation_factor)

    fn on_output(inout self, amplitude: Float64) -> None:
        # In a full engine this would enqueue propagation down tracts.
        pass
