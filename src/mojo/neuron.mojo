from weight import Weight
from slot_engine import SlotEngine

struct Neuron:
    var neuron_id: String
    var slot_engine: SlotEngine
    var slot_limit: Int
    var slots: dict[Int, Weight]
    var outgoing: list[Synapse]  # declared in file using this struct
    var have_last_input: Bool = False
    var last_input_value: Float64 = 0.0
    var last_fired: Bool = False

    fn init(inout self, neuron_id: String, slot_limit: Int = -1) -> None:
        self.neuron_id = neuron_id
        self.slot_engine = SlotEngine()
        self.slot_limit = slot_limit
        self.slots = dict[Int, Weight]()
        self.outgoing = []

    fn connect(inout self, target_index: Int, feedback: Bool = False) -> None:
        from synapse import Synapse
        let s = Synapse(target_index, feedback)
        self.outgoing.append(s)

    fn on_input(inout self, value: Float64, modulation_factor: Float64) -> Bool:
        # Pick/select slot by percent delta.
        var slot_id: Int = 0
        if self.have_last_input:
            slot_id = self.slot_engine.slot_id(self.last_input_value, value, Int(self.slots.size()))
        else:
            slot_id = 0
        # Select or create
        if not self.slots.contains(slot_id):
            if self.slot_limit >= 0 and Int(self.slots.size()) >= self.slot_limit:
                # Reuse 0 if limit reached
                slot_id = 0
            else:
                self.slots[slot_id] = Weight()
        var slot = self.slots[slot_id]
        slot.reinforce(modulation_factor)
        let fired = slot.update_threshold(value)

        self.have_last_input = True
        self.last_input_value = value
        self.last_fired = fired
        self.slots[slot_id] = slot  # writeback
        return fired

    fn on_output(inout self, amplitude: Float64) -> None:
        # Base neuron: no-op; subclasses override.
        pass
