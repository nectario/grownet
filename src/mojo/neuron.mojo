from weight import Weight
from slot_engine import SlotEngine
from lateral_bus import LateralBus
from slot_config import SlotConfig, fixed

struct Neuron:
    var neuron_id: String
    var bus: LateralBus
    var slot_cfg: SlotConfig
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
    var last_slot_used_fallback: Bool = False
    var fallback_streak: Int = 0
    var last_growth_tick: Int64 = -1

    # spatial focus anchors (Phase B)
    var anchor_row: Int = -1
    var anchor_col: Int = -1

    fn init(mut self, neuron_id: String, slot_limit: Int = -1) -> None:
        self.neuron_id = neuron_id
        self.bus = LateralBus()
        self.slot_cfg = fixed(10.0)
        self.slot_engine = SlotEngine()
        self.slot_limit = slot_limit
        self.slots = dict[Int, Weight]()
        self.outgoing = []

    fn connect(mut self, target_index: Int, feedback: Bool = False) -> None:
        from synapse import Synapse
        var syn = Synapse(target_index, feedback)
        self.outgoing.append(syn)

    fn on_input(mut self, value: Float64) -> Bool:
        if not self.focus_set:
            self.focus_anchor = value
            self.focus_set = True

        # Python-parity: use engine helper with strict capacity + fallback
        var slot_identifier: Int = self.slot_engine.select_or_create_slot(self, value)
        self.last_slot_id = slot_identifier

        var at_capacity: Bool = (self.slot_limit >= 0) and (Int(self.slots.size()) >= self.slot_limit)
        var out_of_domain: Bool = (self.slot_limit >= 0) and (slot_identifier >= self.slot_limit)
        var want_new: Bool = not self.slots.contains(slot_identifier)
        self.last_slot_used_fallback = out_of_domain or (at_capacity and want_new)

        if not self.slots.contains(slot_identifier):
            if at_capacity:
                if slot_identifier >= 0 and slot_identifier < self.slot_limit and not self.slots.contains(slot_identifier):
                    # reuse clamped id if empty set (defensive)
                    self.slots[slot_identifier] = Weight()
            else:
                self.slots[slot_identifier] = Weight()

        var selected_weight = self.slots[slot_identifier]
        selected_weight.reinforce(self.bus.modulation_factor)
        var fired: Bool = selected_weight.update_threshold(value)
        self.last_fired = fired
        self.slots[slot_identifier] = selected_weight
        return fired

    fn on_output(mut self, amplitude: Float64) -> None:

        # Base neuron: no-op; subclasses override.
        pass

    fn on_input_2d(mut self, value: Float64, row: Int, col: Int) -> Bool:
        if not self.slot_cfg.spatial_enabled:
            return self.on_input(value)
        var key: Int = self.slot_engine.select_or_create_slot_2d(self, row, col)
        var w = self.slots[key] if self.slots.contains(key) else Weight()
        w.reinforce(self.bus.modulation_factor)
        var fired = w.update_threshold(value)
        self.slots[key] = w
        self.last_fired = fired
        self.have_last_input = True
        self.last_input_value = value
        return fired

    fn freeze_last_slot(mut self) -> Bool:
        if self.last_slot_id < 0:
            return False
        if not self.slots.contains(self.last_slot_id):
            return False
        var slot_weight = self.slots[self.last_slot_id]
        slot_weight.freeze()
        self.slots[self.last_slot_id] = slot_weight
        return True

    fn unfreeze_last_slot(mut self) -> Bool:
        if self.last_slot_id < 0:
            return False
        if not self.slots.contains(self.last_slot_id):
            return False
        var slot_weight = self.slots[self.last_slot_id]
        slot_weight.unfreeze()
        self.slots[self.last_slot_id] = slot_weight
        return True
