# neuron.mojo
import math_utils as mu
from weight import Weight
from bus import LateralBus

# ---- type tags (simple constants) ------------------------------------------
alias EXCITATORY: Int64  = 0
alias INHIBITORY: Int64  = 1
alias MODULATORY: Int64  = 2

# ---- slot policy constants --------------------------------------------------
alias SLOT_FIXED:      Int64 = 0   # uniform width
alias SLOT_NONUNIFORM: Int64 = 1   # edges supplied externally
alias SLOT_ADAPTIVE:   Int64 = 2   # widen on demand

struct Neuron:
    # identity & wiring
    var neuron_id: String
    var bus: LateralBus

    # slots (bin id => Weight)
    var slots: Dict[Int64, Weight]

    # adaptive-threshold memory
    var last_input_seen: Bool
    var last_input_value: F64

    # type & policy
    var type_tag: Int64
    var slot_policy: Int64
    var slot_width_percent: F64
    var nonuniform_edges: Array[F64]   # ascending edges in percent

    # optional slot cap (-1 => unlimited)
    var slot_limit: Int64

    fn init(self, neuron_id: String, bus: LateralBus) -> None:
        self.neuron_id = neuron_id
        self.bus = bus
        self.slots = Dict[Int64, Weight]()
        self.last_input_seen = False
        self.last_input_value = 0.0
        self.type_tag = EXCITATORY
        self.slot_policy = SLOT_FIXED
        self.slot_width_percent = 10.0
        self.nonuniform_edges = Array[F64]()
        self.slot_limit = Int64(-1)

    # ---- public API ---------------------------------------------------------

    fn on_input(self, value: F64) -> None:
        var w = self.select_slot(value)
        w.reinforce(self.bus.modulation_factor, self.bus.inhibition_factor)
        let fired: Bool = w.update_threshold(value)
        if fired:
            self.fire(value)
        self.last_input_seen = True
        self.last_input_value = value

    fn on_output(self, amplitude: F64) -> None:
        # default no-op; subclasses (e.g., OutputNeuron) may use this
        pass

    fn fire(self, input_value: F64) -> None:
        # Default excitatory behaviour; subclasses may override.
        if self.type_tag == INHIBITORY:
            self.bus.inhibition_factor = 0.7   # placeholder
        elif self.type_tag == MODULATORY:
            self.bus.modulation_factor = 1.5   # placeholder
        else:
            # EXCITATORY: fan-out is encoded by Layer/Region wiring in your graph code.
            pass

    # ---- slot selection helpers --------------------------------------------

    fn select_slot(self, input_value: F64) -> Weight:
        var bin_id: Int64 = 0

        if self.last_input_seen and self.last_input_value != 0.0:
            let delta_percent: F64 = mu.percent_delta(self.last_input_value, input_value)
            bin_id = self.bin_for_delta(delta_percent)
        else:
            bin_id = 0

        if self.slots.contains(bin_id):
            return self.slots[bin_id]

        if (self.slot_limit >= 0) and (Int64(self.slots.len) >= self.slot_limit):
            # simple reuse policy: take the first slot
            return self.slots.values()[0]

        var new_w = Weight()
        self.slots[bin_id] = new_w
        return new_w

    fn bin_for_delta(self, delta_percent: F64) -> Int64:
        if self.slot_policy == SLOT_FIXED:
            if delta_percent <= 0.0:
                return 0
            # ceil(delta / width)
            let bucket = Int64((delta_percent + (self.slot_width_percent - 1.0)) / self.slot_width_percent)
            if bucket < 1:
                return 1
            return bucket

        if self.slot_policy == SLOT_NONUNIFORM:
            # edges are ascending; return first index with edge >= delta
            var idx: Int64 = 0
            for edge in self.nonuniform_edges:
                if delta_percent <= edge:
                    return idx
                idx = idx + 1
            return idx  # last bucket

        # SLOT_ADAPTIVE (very simple): start with fixed candidate; if occupied, open a new bucket
        var candidate: Int64 = Int64(delta_percent / self.slot_width_percent)
        if self.slots.contains(candidate):
            var k: Int64 = candidate + 1
            while self.slots.contains(k):
                k = k + 1
            return k
        return candidate

    # ---- scalar logging -----------------------------------------------------

    fn neuron_value(self, mode: String) -> F64:
        if self.slots.len == 0:
            return 0.0

        if mode == "readiness":
            var best_margin: F64 = -1e300
            for pair in self.slots.items():
                let w = pair.value
                let margin: F64 = w.strength_value - w.threshold_value
                if margin > best_margin:
                    best_margin = margin
            return best_margin

        if mode == "firing_rate":
            var total: F64 = 0.0
            for pair in self.slots.items():
                total = total + pair.value.ema_rate
            return total / F64(self.slots.len)

        if mode == "memory":
            var sum_abs: F64 = 0.0
            for pair in self.slots.items():
                let v: F64 = pair.value.strength_value
                sum_abs = sum_abs + (v if v >= 0.0 else -v)
            return sum_abs

        # default
        return self.neuron_value("readiness")

