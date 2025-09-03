# slot_config.mojo — policy + knobs for slot selection

struct SlotConfig:
    # Policies
    alias SLOT_FIXED:       Int64 = 0
    alias SLOT_NONUNIFORM:  Int64 = 1
    alias SLOT_ADAPTIVE:    Int64 = 2

    # knobs
    var slot_policy:        Int64         = SLOT_FIXED
    var slot_width_percent: F64           = 10.0          # for FIXED / ADAPTIVE seed
    var nonuniform_edges:   List[F64]     = []            # ascending, e.g., [2.5, 5.0, 10.0, 20.0]
    var max_slots:          Int64         = -1            # -1 = unbounded
    # temporal-focus knobs
    enum AnchorMode: Int:
        FIRST = 0
        EMA = 1
        WINDOW = 2
        LAST = 3
    var anchor_mode:        AnchorMode    = AnchorMode.FIRST
    var bin_width_pct:      F64           = 10.0
    var epsilon_scale:      F64           = 1e-6
    var recenter_threshold_pct: F64       = 35.0
    var recenter_lock_ticks:    Int       = 20
    var anchor_beta:        F64           = 0.05
    var outlier_growth_threshold_pct: F64 = 60.0
    var slot_limit:         Int           = 16
    # Growth knobs (parity with Python/Java)
    var growth_enabled:     Bool          = True
    var neuron_growth_enabled: Bool       = True
    var neuron_growth_cooldown_ticks: Int = 0
    var fallback_growth_threshold: Int    = 3
    var layer_neuron_limit_default: Int   = -1
