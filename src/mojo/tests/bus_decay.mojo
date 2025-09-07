from lateral_bus import LateralBus

fn check(cond: Bool, msg: String):
    if not cond: raise Error("Test failed: " + msg)

fn test_bus_decay():
    var bus = LateralBus()
    bus.set_inhibition_factor(1.0)
    bus.set_modulation_factor(2.3)
    var before = bus.get_current_step()
    bus.decay()
    check(abs(bus.inhibition_factor - 0.9) < 1e-12, "inhibition decays by 0.9")
    check(bus.modulation_factor == 1.0, "modulation resets to 1.0")
    check(bus.get_current_step() == before + 1, "step increments by 1")

fn main():
    test_bus_decay()
    print("[MOJO] bus_decay passed.")

