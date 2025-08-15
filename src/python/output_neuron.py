from neuron import Neuron
from weight import Weight

class OutputNeuron(Neuron):
    def __init__(self, neuron_id, smoothing=0.2):
        super().__init__(neuron_id, bus=None, slot_cfg=None, slot_limit=1)  # one slot
        self._smoothing = float(smoothing)
        self._last_emitted = 0.0
        self.slots()[0] = Weight()

    def on_input(self, value):
        slot = self.slots()[0]
        # scale reinforcement by modulation and inhibition if provided
        mod = 1.0
        if self.get_bus() is not None:
            mod = self.get_bus().get_modulation_factor()
        slot.reinforce(mod)
        fired = slot.update_threshold(value)
        self.set_fired_last(fired)
        self.set_last_input_value(value)
        if fired:
            self.on_output(value)
        return fired

    def on_output(self, amplitude):
        self._last_emitted = float(amplitude)

    def end_tick(self):
        # decay toward 0
        self._last_emitted *= (1.0 - self._smoothing)

    def get_output_value(self):
        return self._last_emitted
