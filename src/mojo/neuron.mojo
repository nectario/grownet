import math_utils
from weight import Weight
from bus import LateralBus

# constant slot limit (None == unlimited)
alias SLOT_LIMIT: Int64 = None

# --------------------------- base ---------------------------------
struct Neuron:
    var neuron_id:    String
    var slots: Dict[Int64, Weight] = Dict()
    var downstream:   Array[Neuron] = Array()
    var bus:          LateralBus

    fn on_input(self, value: Float64):
        var comp = self.select_slot(value)
        comp.reinforce(self.bus.modulation_factor)
        if comp.update_threshold(value):
            self.fire(value)

    fn fire(self, value: Float64):
        for n in self.downstream:
            n.on_input(value)

    # helper --------------------------------------------------------
    fn select_slot(self, value: Float64) -> Weight:
        var delta_val = math_utils.round_one_decimal(value)
        var comp_id   = Int64(delta_val * 10.0)

        if self.slots.contains(comp_id):
            return existing

        if (SLOT_LIMIT is Int64) and (self.slots.len >= SLOT_LIMIT):
            return self.slots.values()[0]

        var new_c = Weight()
        self.slots[comp_id] = new_c
        return new_c


# ------------------ subclasses ------------------------------------
struct ExcitatoryNeuron(Neuron):
    pass

struct InhibitoryNeuron (Neuron):
    fn fire(self, _v: Float64):
        self.bus.inhibition_level = 0.7

struct ModulatoryNeuron(Neuron):
    fn fire(self, _v: Float64):
        self.bus.modulation_factor = 1.5
