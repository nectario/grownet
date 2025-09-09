from layer import Layer
from slot_config import SlotConfig
from weight import Weight

fn check(cond: Bool, msg: String):
    if not cond:
        raise Error("Test failed: " + msg)

fn test_defaults_preserve_behavior():
    var layer = Layer(1, 0, 0)
    var neuron = layer.get_neurons()[0]
    neuron.slot_cfg.slot_limit = 1
    neuron.slot_limit = 1
    layer.forward(1.0)
    layer.end_tick()
    var i = 0
    while i < 3:
        layer.forward(1.8)
        layer.end_tick()
        i = i + 1
    check(neuron.fallback_streak == 0, "streak resets after growth")

fn test_same_missing_slot_guard_blocks_alternation():
    var layer = Layer(1, 0, 0)
    var neuron = layer.get_neurons()[0]
    neuron.slot_cfg.slot_limit = 1
    neuron.slot_limit = 1
    neuron.slot_cfg.fallback_growth_requires_same_missing_slot = True
    layer.forward(1.0)
    layer.end_tick()
    var seq = [2.0, 1.8, 2.0, 1.8, 2.0, 1.8]
    var idx = 0
    while idx < seq.len:
        layer.forward(seq[idx])
        layer.end_tick()
        idx = idx + 1
    check(neuron.fallback_streak <= 1, "alternating missing ids should not accumulate")

fn test_min_delta_gate_blocks_small_deltas():
    var layer = Layer(1, 0, 0)
    var neuron = layer.get_neurons()[0]
    neuron.slot_cfg.slot_limit = 1
    neuron.slot_limit = 1
    neuron.slot_cfg.min_delta_pct_for_growth = 70.0
    layer.forward(1.0)
    layer.end_tick()
    var i = 0
    while i < 3:
        layer.forward(1.6)
        layer.end_tick()
        i = i + 1
    check(neuron.fallback_streak == 0, "small deltas should not count")
    i = 0
    while i < 3:
        layer.forward(1.8)
        layer.end_tick()
        i = i + 1
    check(neuron.fallback_streak == 0, "after growth streak resets")

fn main():
    test_defaults_preserve_behavior()
    test_same_missing_slot_guard_blocks_alternation()
    test_min_delta_gate_blocks_small_deltas()
    print("[MOJO] growth_guards tests passed.")
