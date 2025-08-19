// src/mojo/tests/pulse_and_binding.mojo
from lateral_bus import LateralBus
from region import Region

fn check(cond: Bool, msg: String):
    if not cond:
        raise Error("Test failed: " + msg)

# Pulse semantics via LateralBus (works today even if Region pulses are not wired yet).
fn test_pulse_decay_on_bus():
    var bus = LateralBus()
    bus.set_modulation_factor(1.5)
    bus.set_inhibition_factor(0.7)
    bus.decay()
    # Mojo bus drifts toward 1.0 for both factors
    check(abs(bus.modulation_factor - 1.0) < 1e-12, "modulation resets toward 1.0")
    # Inhibition moves toward 1.0 by decay_rate (default 0.10); exact value depends on current impl
    # We just confirm it moved closer to 1.0
    check(bus.inhibition_factor > 0.7, "inhibition moves toward 1.0")

# Multi-layer binding placeholder: compiles and runs; assertion enabled once Region.tick implements delivery.
fn test_multi_layer_input_binding_pending():
    var region = Region("t")
    let l0 = region.add_layer(1,0,0)
    let l1 = region.add_layer(1,0,0)
    region.bind_input("x", [l0, l1])
    let m = region.tick("x", 1.0)
    print("[MOJO] multiLayerBinding delivered=", m.deliveredEvents)
    # TODO: enable strict assertion when Region.tick aggregates events
    # check(m.deliveredEvents == 2, "deliveredEvents should equal 2 once Region.tick is complete")

fn main():
    test_pulse_decay_on_bus()
    test_multi_layer_input_binding_pending()
    print("[MOJO] Pulse/Binding tests executed.")
