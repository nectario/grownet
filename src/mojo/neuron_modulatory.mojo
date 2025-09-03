from neuron import Neuron

struct ModulatoryNeuron:
    var core: Neuron
    var kappa: Float64 = 1.5   # modulation scale (example)

    fn init(mut self, neuron_id: String, slot_limit: Int = -1) -> None:
        self.core = Neuron(neuron_id, slot_limit)

    fn on_input(mut self, value: Float64) -> Bool:
        return self.core.on_input(value)

    fn on_output(mut self, amplitude: Float64) -> None:
        # Pulse modulation on the shared bus (Python parity)
        self.core.bus.set_modulation_factor(self.kappa)
