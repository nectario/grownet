from neuron import Neuron

struct InhibitoryNeuron:
    var core: Neuron
    var gamma: Float64 = 0.7   # inhibition multiplier (example)

    fn init(mut self, neuron_id: String, slot_limit: Int = -1) -> None:
        self.core = Neuron(neuron_id, slot_limit)

    fn on_input(mut self, value: Float64) -> Bool:
        return self.core.on_input(value)

    fn on_output(mut self, amplitude: Float64) -> None:
        # Pulse inhibition on the shared bus (Python parity)
        self.core.bus.set_inhibition_factor(self.gamma)
