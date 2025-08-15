from slot_config import SlotPolicy
from weight import Weight

class SlotEngine:
    def __init__(self, cfg):
        self._cfg = cfg

    def slot_id(self, last_input, current_input, known_slots):
        # map percent delta into an integer slot id (bin)
        if self._cfg.policy == SlotPolicy.FIXED:
            if last_input == 0:
                return 0
            delta_percent = abs(current_input - last_input) / max(1e-9, abs(last_input)) * 100.0
            w = max(1.0, self._cfg.fixed_delta_percent)
            return int(delta_percent // w)
        elif self._cfg.policy == SlotPolicy.NONUNIFORM:
            if last_input == 0:
                return 0
            dp = abs(current_input - last_input) / max(1e-9, abs(last_input)) * 100.0
            for i, edge in enumerate(self._cfg.custom_edges):
                if dp < edge:
                    return i
            return len(self._cfg.custom_edges)
        else:
            # ADAPTIVE or unknown: collapse everything to slot 0
            return 0

    def select_or_create_slot(self, neuron, input_value, tick_count=0):
        # neuron must expose: has_last_input(), get_last_input_value(), slots dict
        if neuron.has_last_input():
            sid = self.slot_id(neuron.get_last_input_value(), input_value, len(neuron.slots()))
        else:
            sid = 0
        if sid not in neuron.slots():
            neuron.slots()[sid] = Weight()
        wt = neuron.slots()[sid]
        wt.mark_touched(tick_count)
        return wt
