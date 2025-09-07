from region import Region
from growth import GrowthPolicy


def test_region_grows_at_most_one_layer_per_tick_and_tracks_step():
    region = Region("one-growth-per-tick")

    # Build 2D input and a small hidden layer; connect via windowed wiring
    in_idx = region.add_input_layer_2d(4, 4, 1.0, 0.01)
    hid_idx = region.add_layer(6, 0, 0)
    region.connect_layers_windowed(in_idx, hid_idx, 2, 2, 1, 1, "valid")
    region.bind_input_2d("img", 4, 4, 1.0, 0.01, [in_idx])

    # Aggressive policy to trigger region growth quickly; cooldown off to test per-tick cap
    policy = GrowthPolicy(
        enable_layer_growth=True,
        max_total_layers=64,
        avg_slots_threshold=0.0,
        percent_neurons_at_cap_threshold=0.0,
        layer_cooldown_ticks=0,
    )
    region.set_growth_policy(policy)

    prev_layers = len(region.get_layers())
    for _ in range(5):
        metrics = region.tick_2d("img", [[1.0]*4 for _ in range(4)])
        now_layers = len(region.get_layers())
        # At most one growth per tick
        assert now_layers - prev_layers in (0, 1)
        if now_layers > prev_layers:
            # last_layer_growth_step must match the layer bus current step
            step = region.get_layers()[0].get_bus().get_current_step()
            assert getattr(region, "last_layer_growth_step", -1) == step
        prev_layers = now_layers

