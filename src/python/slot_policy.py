class SlotPolicyConfig:
    def __init__(self,
                 mode: str = "fixed",
                 slot_width_percent: float = 0.10,
                 multires_widths: list[float] | None = None,
                 boundary_refine_hits: int = 5,
                 target_active_low: int = 6,
                 target_active_high: int = 12,
                 min_slot_width: float = 0.01,
                 max_slot_width: float = 0.20,
                 adjust_cooldown_ticks: int = 200,
                 adjust_factor_up: float = 1.2,
                 adjust_factor_down: float = 0.9,
                 nonuniform_schedule: list[float] | None = None):
        """
        mode: "fixed" | "multi_resolution" | "adaptive"
        slot_width_percent: used when mode == "fixed" or as initial width in adaptive
        multires_widths: e.g., [0.10, 0.05, 0.02] (coarse->fine)
        boundary_refine_hits: times landing near a boundary before refining
        target_active_[low/high]: desired range of active slots per neuron (adaptive)
        min/max_slot_width: clamp for adaptive
        adjust_cooldown_ticks: only adjust width every N ticks (adaptive)
        adjust_factor_*: multiplicative step for width
        nonuniform_schedule: optional per-slot creation width schedule, e.g., [0.10,0.10,0.08,0.05,0.05,0.02]
        """
        self.mode = mode
        self.slot_width_percent = slot_width_percent
        self.multires_widths = multires_widths or [0.10, 0.05, 0.02]
        self.boundary_refine_hits = boundary_refine_hits
        self.target_active_low = target_active_low
        self.target_active_high = target_active_high
        self.min_slot_width = min_slot_width
        self.max_slot_width = max_slot_width
        self.adjust_cooldown_ticks = adjust_cooldown_ticks
        self.adjust_factor_up = adjust_factor_up
        self.adjust_factor_down = adjust_factor_down
        self.nonuniform_schedule = nonuniform_schedule  # optional
