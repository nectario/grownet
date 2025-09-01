# input_neuron.mojo — single-slot sensory neuron (keeps contract)

from neuron import Neuron
from weight import Weight

struct InputNeuron(Neuron):
    fn on_input(self, value: F64) -> Bool:
        var slot: Weight
        if self.slots.len == 0:
            slot = Weight()
            self.slots[0] = slot
        else:
            slot = self.slots[0]

        slot.reinforce(self.bus.modulation_factor)
        var fired = slot.update_threshold(value)
        if fired:
            self.fire(value)

        self.have_last_input  = True
        self.last_input_value = value
        return fired
