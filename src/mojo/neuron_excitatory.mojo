from neuron import Neuron

struct ExcitatoryNeuron:
    var core: Neuron

    fn init(mut self, neuron_id: String, slot_limit: Int = -1) -> None:
        self.core = Neuron(neuron_id, slot_limit)

    fn on_input(mut self, value: Float64) -> Bool:
        return self.core.on_input(value)

    fn on_output(mut self, amplitude: Float64) -> None:
        # In a full engine this would enqueue propagation down tracts.
        pass
