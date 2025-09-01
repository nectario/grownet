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

    # temporal focus state
    var focus_anchor: Float64 = 0.0
    var focus_set: Bool = False
    var focus_lock_until_tick: Int = 0
    var last_fired: Bool = False
    var last_slot_id: Int = -1  # remember last selected slot id

    # spatial focus anchors (Phase B)
    var anchor_row: Int = -1
    var anchor_col: Int = -1

    fn init(mut self, neuron_id: String, slot_limit: Int = -1) -> None:
        self.neuron_id = neuron_id
        self.slot_engine = SlotEngine()
        self.slot_limit = slot_limit
        self.slots = dict[Int, Weight]()
        self.outgoing = []

    fn connect(mut self, target_index: Int, feedback: Bool = False) -> None:
        from synapse import Synapse
        var syn = Synapse(target_index, feedback)
        self.outgoing.append(syn)

    fn on_input(mut self, value: Float64, modulation_factor: Float64) -> Bool:
        if not self.focus_set:
            self.focus_anchor = value
            self.focus_set = True

        var bin_width_pct: Float64 = 10.0
        var epsilon_scale: Float64 = 1e-6
        var slot_identifier: Int = self.slot_engine.select_anchor_slot_id(
            self.focus_anchor, value, bin_width_pct, epsilon_scale
        )
        self.last_slot_id = slot_identifier

        if not self.slots.contains(slot_identifier):
            if self.slot_limit >= 0 and Int(self.slots.size()) >= self.slot_limit:
                if slot_identifier >= self.slot_limit:
                    slot_identifier = self.slot_limit - 1
                if not self.slots.contains(slot_identifier):
                    self.slots[slot_identifier] = Weight()
            else:
                self.slots[slot_identifier] = Weight()

        var selected_weight = self.slots[slot_identifier]
        selected_weight.reinforce(modulation_factor)
        var fired: Bool = selected_weight.update_threshold(value)
        self.last_fired = fired
        self.slots[slot_identifier] = selected_weight
        return fired

    fn on_output(mut self, amplitude: Float64) -> None:

        # Base neuron: no-op; subclasses override.
        pass

    fn on_input_2d(mut self, value: Float64, row: Int, col: Int, modulation_factor: Float64) -> Bool:
        # Default: reuse scalar path
        return self.on_input(value, modulation_factor)

    fn freeze_last_slot(mut self) -> Bool:
        if self.last_slot_id < 0:
            return False
        if not self.slots.contains(self.last_slot_id):
            return False
        var w = self.slots[self.last_slot_id]
        w.freeze()
        self.slots[self.last_slot_id] = w
        return True

    fn unfreeze_last_slot(mut self) -> Bool:
        if self.last_slot_id < 0:
            return False
        if not self.slots.contains(self.last_slot_id):
            return False
        var w = self.slots[self.last_slot_id]
        w.unfreeze()
        self.slots[self.last_slot_id] = w
        return True
