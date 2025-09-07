from region import Region

fn check(cond: Bool, msg: String):
    if not cond: raise Error("Test failed: " + msg)

fn test_one_growth_per_tick():
    var region = Region("one-growth")
    var in_idx = region.add_input_layer_2d(4,4,1.0,0.01)
    var hid_idx = region.add_layer(6,0,0)
    _ = region.connect_layers_windowed(in_idx, hid_idx, 2,2,1,1, "valid")
    region.bind_input_2d("img", 4,4,1.0,0.01, [in_idx])

    # aggressive policy
    var policy = region.get_growth_policy()
    policy.enable_layer_growth = True
    policy.max_layers = 64
    policy.avg_slots_threshold = 0.0
    policy.layer_cooldown_ticks = 0
    region.set_growth_policy(policy)

    var prev_layers = region.get_layers().len
    var step = 0
    while step < 5:
        var frame = [[1.0,1.0,1.0,1.0], [1.0,1.0,1.0,1.0], [1.0,1.0,1.0,1.0], [1.0,1.0,1.0,1.0]]
        _ = region.tick_image("img", frame)
        var now_layers = region.get_layers().len
        var delta = now_layers - prev_layers
        check(delta == 0 or delta == 1, "at most one growth per tick")
        prev_layers = now_layers
        step = step + 1

fn main():
    test_one_growth_per_tick()
    print("[MOJO] one_growth_per_tick passed.")

