# output_neuron.mojo
# Single-slot exit neuron:
# - Also a single-slot receiver (slot 0)
# - On threshold crossing, records the amplitude and calls `on_output`
#   so external code (dashboards/actuators) can hook into the emission.

from neuron import Neuron, EXCITATORY
from weight import Weight
from bus import LateralBus

struct OutputNeuron(Neuron):
    var last_emitted: F64 = 0.0

    fn init(self, neuron_id: String, bus: LateralBus) -> None:
        self.neuron_id = neuron_id
        self.bus = bus
        self.type_tag = EXCITATORY  # behavior-wise, exits are excitatory sinks

    # Hook for external systems (e.g., UI dashboards, actuators).
    # Override in user code if you want actual side-effects.
    fn on_output(self, amplitude: F64) -> None:
        pass

    fn on_input(self, input_value: F64) -> None:
        # Always use slot 0 (single-slot semantics).
        if not self.slots.contains(0):
            self.slots[0] = Weight()

        var slot0 = self.slots[0]
        slot0.reinforce(self.bus.modulation_factor)
        let fired: Bool = slot0.update_threshold(input_value)
        self.slots[0] = slot0  # persist mutations

        if fired:
            self.last_emitted = input_value
            self.on_output(input_value)

        self.last_input_seen = True
        self.last_input_value = input_value
