# input_neuron.mojo
# Single-slot entry neuron:
# - Treats all inputs as belonging to slot 0 (no delta-based binning)
# - Uses the base Weight adaptive-threshold rule
# - Calls `fire` only when the slot crosses threshold (same as other neurons)

from neuron import Neuron, EXCITATORY
from weight import Weight
from bus import LateralBus

struct InputNeuron(Neuron):
    fn init(self, neuron_id: String, bus: LateralBus) -> None:
        self.neuron_id = neuron_id
        self.bus = bus
        self.type_tag = EXCITATORY  # entry neurons are excitatory by default

    fn on_input(self, input_value: F64) -> None:
        # Always operate on slot 0 (single-slot semantics).
        if not self.slots.contains(0):
            self.slots[0] = Weight()

        # Work on a local variable, then write back to ensure persistence.
        var slot0 = self.slots[0]
        slot0.reinforce(self.bus.modulation_factor)
        let fired: Bool = slot0.update_threshold(input_value)
        self.slots[0] = slot0  # persist mutations

        if fired:
            self.fire(input_value)

        # Bookkeeping for completeness (even though delta isn't used here).
        self.last_input_seen = True
        self.last_input_value = input_value
