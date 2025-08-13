# slot_policy.mojo
struct SlotPolicyConfig:
    var mode: String                # "fixed", "multi_resolution", "adaptive"
    var slot_width_percent: Float64
    var multires_widths: List[Float64]
    var boundary_refine_hits: Int64
    var target_active_low: Int64
    var target_active_high: Int64
    var min_slot_width: Float64
    var max_slot_width: Float64
    var adjust_cooldown_ticks: Int64
    var adjust_factor_up: Float64
    var adjust_factor_down: Float64
    var nonuniform_schedule: List[Float64]   # empty list = off

    fn __init__(mut self ):
        self.mode = "fixed"
        self.slot_width_percent = 0.10
        self.multires_widths = [0.10, 0.05, 0.02]
        self.boundary_refine_hits = 5
        self.target_active_low = 6
        self.target_active_high = 12
        self.min_slot_width = 0.01
        self.max_slot_width = 0.20
        self.adjust_cooldown_ticks = 200
        self.adjust_factor_up = 1.2
        self.adjust_factor_down = 0.9
        self.nonuniform_schedule = []
