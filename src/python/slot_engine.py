from slot_config import SlotPolicy
from weight import Weight

class SlotEngine:
    def __init__(self, cfg):
        self.cfg = cfg

    def slot_id(self, last_input, current_input, known_slots):
        # map percent delta into an integer slot id (bin)
        if self.cfg.policy == SlotPolicy.FIXED:
            if last_input == 0:
                return 0
            delta_percent = abs(current_input - last_input) / max(1e-9, abs(last_input)) * 100.0
            w = max(1.0, self.cfg.fixed_delta_percent)
            return int(delta_percent // w)
        elif self.cfg.policy == SlotPolicy.NONUNIFORM:
            if last_input == 0:
                return 0
            dp = abs(current_input - last_input) / max(1e-9, abs(last_input)) * 100.0
            for i, edge in enumerate(self.cfg.custom_edges):
                if dp < edge:
                    return i
            return len(self.cfg.custom_edges)
        else:
            # ADAPTIVE or unknown: collapse everything to slot 0
            return 0

    def select_or_create_slot(self, neuron, input_value, tick_count=0):
        cfg = self.cfg
        # FIRST-anchor: set anchor once
        if not getattr(neuron, "focus_set", False) and getattr(cfg, "anchor_mode", "FIRST") == "FIRST":
            neuron.focus_anchor = float(input_value)
            neuron.focus_set = True

        anchor = float(getattr(neuron, "focus_anchor", 0.0))
        eps = max(1e-12, float(getattr(cfg, "epsilon_scale", 1e-6)))
        denom = max(abs(anchor), eps)
        delta_pct = abs(float(input_value) - anchor) / denom * 100.0
        bin_w = max(0.1, float(getattr(cfg, "bin_width_pct", 10.0)))
        sid = int(delta_pct // bin_w)

        # clamp to slot_limit, ensure existence
        limit = int(getattr(cfg, "slot_limit", 16))
        if limit > 0 and sid >= limit:
            sid = limit - 1
        slots = neuron.slots
        if sid not in slots:
            if limit > 0 and len(slots) >= limit:
                # reuse last id within [0, limit-1]
                sid = min(sid, limit - 1)
                if sid not in slots:
                    slots[sid] = Weight()
            else:
                slots[sid] = Weight()
        return slots[sid]
