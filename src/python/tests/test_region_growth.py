from region import Region
from growth import GrowthPolicy


def make_region_for_growth():
    r = Region("region_growth_smoke")
    lin = r.add_input_layer_2d(4, 4, gain=1.0, epsilon_fire=0.01)
    hid = r.add_layer(excitatory_count=6, inhibitory_count=0, modulatory_count=0)
    r.connect_layers_windowed(lin, hid, kernel_h=2, kernel_w=2, stride_h=2, stride_w=2, padding="valid")
    r.bind_input("img", [lin])

    # Turn on spatial focus for hidden and cap slots to push pressure
    L = r.get_layers()[hid]
    for n in L.get_neurons():
        n.slot_cfg.spatial_enabled = True
        n.slot_cfg.row_bin_width_pct = 10.0
        n.slot_cfg.col_bin_width_pct = 10.0
        n.slot_limit = 1
    return r, lin, hid


def test_region_adds_layer_under_pressure():
    r, lin, hid = make_region_for_growth()
    # Aggressive policy: minimal thresholds, no cooldown
    pol = GrowthPolicy(
        enable_layer_growth=True,
        max_total_layers=32,
        avg_slots_threshold=1.0,
        percent_neurons_at_cap_threshold=0.0,
        layer_cooldown_ticks=0,
        new_layer_excitatory_count=3,
        wire_probability=1.0,
    )
    r.set_growth_policy(pol)
    base_layers = len(r.get_layers())

    frames = [
        [[0, 1, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]],
        [[0, 0, 1, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]],
        [[0, 0, 0, 1], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]],
    ]
    for f in frames:
        r.tick_2d("img", f)

    assert len(r.get_layers()) > base_layers

