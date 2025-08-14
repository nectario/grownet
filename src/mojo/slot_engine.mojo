# slot_engine.mojo — pure functions to map inputs → slot ids

from math_utils import abs_val, floor_int
from slot_config import SlotConfig

struct SlotEngine:
    var cfg: SlotConfig

    fn init(cfg: SlotConfig) -> None:
        self.cfg = cfg

    fn slot_id(self, last_input: F64, new_input: F64, slots_len: Int64) -> Int64:
        # percent delta vs last input (T0 bootstrap handled by caller)
        var delta_percent: F64 = 0.0
        if last_input != 0.0:
            delta_percent = abs_val(new_input - last_input) / abs_val(last_input) * 100.0

        if self.cfg.slot_policy == SlotConfig.SLOT_FIXED:
            return self.fixed_bucket(delta_percent, slots_len)

        if self.cfg.slot_policy == SlotConfig.SLOT_NONUNIFORM:
            return self.nonuniform_bucket(delta_percent, slots_len)

        # SLOT_ADAPTIVE (seed with fixed; allow overflow if occupied)
        return self.adaptive_bucket(delta_percent, slots_len)

    fn fixed_bucket(self, delta_percent: F64, _slots_len: Int64) -> Int64:
        if delta_percent <= 0.0:
            return 0
        let k = floor_int((delta_percent + (self.cfg.slot_width_percent - 1.0)) / self.cfg.slot_width_percent)
        return k

    fn nonuniform_bucket(self, delta_percent: F64, _slots_len: Int64) -> Int64:
        var idx: Int64 = 0
        for edge in self.cfg.nonuniform_edges:
            if delta_percent <= edge:
                return idx
            idx = idx + 1
        return idx  # last/open bucket

    fn adaptive_bucket(self, delta_percent: F64, slots_len: Int64) -> Int64:
        # start with the fixed id, if that "index" is already occupied the
        # caller may still create a new bucket; we just return the base id here.
        return self.fixed_bucket(delta_percent, slots_len)
