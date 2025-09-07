# File: src/mojo/tests/region_growth_or_trigger_test.mojo
# ADAPT API names to your Mojo codebase. Uses descriptive identifiers and typed params.

struct TestRunner:
    fn expect_eq[T](self, left: T, right: T, message: String):
        if left != right:
            print("ASSERT EQ FAILED: ", message, " left=", left, " right=", right)
            raise Error(message)

    fn expect_true(self, condition: Bool, message: String):
        if not condition:
            print("ASSERT TRUE FAILED: ", message)
            raise Error(message)

fn drive_tick_with_uniform_frame(region: any, input_layer_index: Int, height: Int, width: Int, value: Float64):
    var frame = [Float64](repeating: 0.0, count: height * width)
    var row_index = 0
    while row_index < height:
        var col_index = 0
        while col_index < width:
            frame[row_index * width + col_index] = value
            col_index = col_index + 1
        row_index = row_index + 1
    region.set_input_frame(input_layer_index, frame, height, width)   # ADAPT
    region.tick_2d(height, width)                                     # ADAPT: tick_image / tick2d

fn test_region_growth_or_trigger_single_growth():
    let t = TestRunner()

    var region = Region(name: "mojo_or_trigger")   # ADAPT ctor
    let height = 4
    let width = 4
    let input_layer_index = region.add_input_2d_layer(height, width)  # ADAPT

    # Slot config: capacity 1 (strict)
    var slot_cfg = SlotConfig()                                       # ADAPT
    slot_cfg.slot_limit = 1
    slot_cfg.growth_enabled = True
    slot_cfg.neuron_growth_enabled = True
    region.layer(input_layer_index).set_slot_config(slot_cfg)         # ADAPT

    # Growth policy: enable OR‑trigger via percent_at_cap_fallback_threshold
    var policy = GrowthPolicy()                                       # ADAPT
    policy.avg_slots_threshold = 1_000_000_000.0
    policy.percent_at_cap_fallback_threshold = 0.75
    policy.layer_cooldown_ticks = 0
    policy.max_layers = 32
    region.set_growth_policy(policy)                                  # ADAPT

    let layer_count_before = region.layer_count()                     # ADAPT

    drive_tick_with_uniform_frame(region, input_layer_index, height, width, 1.0)
    drive_tick_with_uniform_frame(region, input_layer_index, height, width, 0.2)

    let layer_count_after = region.layer_count()
    t.expect_eq(layer_count_after, layer_count_before + 1, "Exactly one layer must be added in the tick where OR‑trigger holds")

    let current_step = region.bus.get_current_step()                  # ADAPT accessor
    let last_growth_step = region.get_last_layer_growth_step()        # ADAPT
    t.expect_eq(last_growth_step, current_step, "last_layer_growth_step must equal bus current_step")
