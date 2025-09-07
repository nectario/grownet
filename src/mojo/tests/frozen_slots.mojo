from layer import Layer

fn check(cond: Bool, msg: String):
    if not cond: raise Error("Test failed: " + msg)

fn test_frozen_slots():
    var layer = Layer(1, 0, 0)
    var neurons = layer.get_neurons()
    var neuron = neurons[0]

    # Establish a single slot
    layer.forward(0.6)
    layer.end_tick()
    var slots_before = Int(neuron.slots.size())
    check(slots_before == 1, "expects exactly one slot after first drive")

    # Freeze last slot and drive; strength/threshold should not change
    var slot_id = neuron.last_slot_id
    var slot_weight = neuron.slots[slot_id]
    var strength0 = slot_weight.get_strength_value()
    var frozen_ok = neuron.freeze_last_slot()
    check(frozen_ok, "freeze_last_slot returns true")
    layer.forward(0.9)
    layer.end_tick()
    var slot_weight_frozen = neuron.slots[slot_id]
    check(slot_weight_frozen.get_strength_value() == strength0, "strength does not change while frozen")

    # Unfreeze and drive; adaptation should resume (strength increases)
    var unfreeze_ok = neuron.unfreeze_last_slot()
    check(unfreeze_ok, "unfreeze_last_slot returns true")
    layer.forward(0.85)
    layer.end_tick()
    var slot_weight_after = neuron.slots[slot_id]
    check(slot_weight_after.get_strength_value() > strength0, "strength increases after unfreeze")

fn main():
    test_frozen_slots()
    print("[MOJO] frozen_slots passed.")

