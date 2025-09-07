class SlotPolicy:
    FIXED = "fixed"
    NONUNIFORM = "nonuniform"
    ADAPTIVE = "adaptive"

class SlotConfig:
    def __init__(self, policy=SlotPolicy.FIXED, fixed_delta_percent=10.0, custom_edges=None):
        self.policy = policy
        self.fixed_delta_percent = float(fixed_delta_percent)
        self.custom_edges = list(custom_edges) if custom_edges else []

    # Temporal focus knobs (class-level defaults)
    anchor_mode = "FIRST"                 # FIRST | EMA | WINDOW | LAST
    bin_width_pct = 10.0                  # percent delta per slot bin
    epsilon_scale = 1e-6                  # guard for zero/near-zero anchors
    recenter_threshold_pct = 35.0         # when to consider re-anchoring
    recenter_lock_ticks = 20              # cooldown on re-anchoring
    anchor_beta = 0.05                    # EMA smoothing for EMA/WINDOW
    outlier_growth_threshold_pct = 60.0   # threshold for neuron growth hooks
    slot_limit = 16                       # cap slots per neuron (strict in v5)

    # Spatial focus knobs (Phase B)
    # When enabled on destination neurons/layers, slotting uses 2D anchors/bins.
    spatial_enabled = False               # off by default; opt-in per layer/neuron
    row_bin_width_pct = 100.0             # bin width for row deltas (percent)
    col_bin_width_pct = 100.0             # bin width for col deltas (percent)
    # anchor_mode is reused; support "ORIGIN" for spatial (anchor at (0,0)).

    # ---------------- Growth knobs ----------------
    # Global toggle (checked per neuron via its slot_cfg)
    growth_enabled = True
    # Escalation: slots -> neurons -> (optional) layers
    neuron_growth_enabled = True
    layer_growth_enabled = False  # off by default; conservative
    # If select/create hits the fallback bin this many consecutive times, request neuron growth
    fallback_growth_threshold = 3
    # Cooldown (ticks) to avoid thrash between growth events
    neuron_growth_cooldown_ticks = 0
    # Layer-level default max neurons (-1 = unlimited). A Layer may override.
    layer_neuron_limit_default = -1

def fixed(delta_percent=10.0):
    return SlotConfig(SlotPolicy.FIXED, fixed_delta_percent=delta_percent)

def nonuniform(edges_percent):
    return SlotConfig(SlotPolicy.NONUNIFORM, custom_edges=list(edges_percent))

def adaptive():
    # placeholder; policy hook for future work
    return SlotConfig(SlotPolicy.ADAPTIVE)
