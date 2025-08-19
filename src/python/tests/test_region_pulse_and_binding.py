# src/python/test/test_region_pulse_and_binding.py
from region import Region

def test_multi_layer_input_binding():
    region = Region("t")
    layer_a = region.add_layer(1, 0, 0)
    layer_b = region.add_layer(1, 0, 0)
    region.bind_input("x", [layer_a, layer_b])
    metrics = region.tick("x", 1.0)
    assert getattr(metrics, "deliveredEvents", None) == 2

def test_pulse_checks():
    region = Region("t")
    layer_idx = region.add_layer(1, 0, 0)
    region.bind_input("x", [layer_idx])

    # Issue pulses via Region API (fan-out to layer buses).
    region.pulse_modulation(1.5)
    region.pulse_inhibition(0.7)

    # Grab the layer bus to inspect post-tick state.
    layer = region.get_layers()[layer_idx]
    bus = layer.get_bus()

    m = region.tick("x", 0.5)
    # After end_of_tick: modulation resets to 1.0; inhibition decays multiplicatively (default 0.9)
    assert abs(bus.get_modulation_factor() - 1.0) < 1e-12
    expected_inh = 0.7 * 0.9
    assert abs(bus.get_inhibition_factor() - expected_inh) < 1e-9
