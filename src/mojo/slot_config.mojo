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
