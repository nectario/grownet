from neuron import Neuron
from weight import Weight

class InputNeuron(Neuron):
    def __init__(self, neuron_id, gain=1.0, epsilon_fire=0.01):
        super().__init__(neuron_id, bus=None, slot_cfg=None, slot_limit=1)  # single-slot sink
        self._gain = float(gain)
        self._epsilon_fire = float(epsilon_fire)
        # ensure slot 0 exists
        self.slots()[0] = Weight()

    def on_input(self, value):
        effective = self._gain * float(value)
        slot = self.slots()[0]
        # T0 threshold init
        if not slot.is_first_seen():
            slot.set_threshold_value(max(0.0, abs(effective) * (1.0 - self._epsilon_fire)))
            slot.set_first_seen(True)
        # reinforcement with modulation
        mod = 1.0
        if self.get_bus() is not None:
            mod = self.get_bus().get_modulation_factor()
        slot.reinforce(mod)
        fired = slot.update_threshold(effective)
        self.set_fired_last(fired)
        self.set_last_input_value(effective)
        if fired:
            self.on_output(effective)
        return fired

    def on_output(self, amplitude):
        # input neurons don't fan out by themselves; # Layer/Tract handles routing
        pass
