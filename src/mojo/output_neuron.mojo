# output_neuron.mojo — single-slot sink + external exposure via on_output

from neuron import Neuron
from weight import Weight

struct OutputNeuron(Neuron):
    var last_emitted: F64

    fn init(neuron_id: String, bus: LateralBus) -> None:
        super.init(neuron_id, bus)
        self.last_emitted = 0.0

    fn on_output(self, amplitude: F64) -> None:
        self.last_emitted = amplitude

    fn on_input(self, value: F64) -> Bool:
        # keep contract: accept input, store, and report via on_output
        var slot: Weight
        if self.slots.len == 0:
            slot = Weight()
            self.slots[0] = slot
        else:
            slot = self.slots[0]

        slot.reinforce(self.bus.modulation_factor)
        var fired = slot.update_threshold(value)
        if fired:
            self.on_output(value)
        self.have_last_input = True
        self.last_input_value = value
        return fired
