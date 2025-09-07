from lateral_bus import LateralBus


def test_lateral_bus_decay_semantics():
    bus = LateralBus()
    # Set some non-default values
    bus.set_inhibition_factor(1.0)
    bus.set_modulation_factor(2.5)
    step_before = bus.get_current_step()

    bus.decay()

    # Inhibition decays multiplicatively by default (~0.90)
    assert abs(bus.get_inhibition_factor() - 0.9) < 1e-9
    # Modulation resets to neutral 1.0
    assert bus.get_modulation_factor() == 1.0
    # Tick counter increments exactly once
    assert bus.get_current_step() == step_before + 1

