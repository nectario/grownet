from __future__ import annotations
from typing import Dict
from slot_config import SlotConfig, SlotPolicy
from weight import Weight
from math_utils import round_one_decimal
from neuron import Neuron

class SlotEngine:
    def __init__(self, config: SlotConfig) -> None:
        self.config = config

    def compute_bin_for_delta_percent(self, delta_percent: float, slots: Dict[int, Weight]) -> int:
        if self.config.policy == SlotPolicy.FIXED:
            if delta_percent <= 0.0:
                return 0
            return int(delta_percent // max(self.config.slot_width_percent, 1e-9))

        if self.config.policy == SlotPolicy.NONUNIFORM:
            for index, edge in enumerate(self.config.nonuniform_edges):
                if delta_percent <= edge:
                    return index
            return len(self.config.nonuniform_edges)

        # ADAPTIVE
        candidate = int(delta_percent // max(self.config.slot_width_percent, 1e-9))
        while candidate in slots:
            candidate += 1
        return candidate

    def select_or_create_slot(self, neuron: "Neuron", input_value: float) -> Weight:
        # Determine bin
        if not neuron.have_last_input:
            bin_id = 0
        else:
            last = neuron.last_input_value
            if abs(last) < 1e-9:
                delta_percent = 0.0
            else:
                delta_percent = abs(input_value - last) / abs(last) * 100.0
            bin_id = self.compute_bin_for_delta_percent(round_one_decimal(delta_percent), neuron.slots)

        # Reuse or create (respect capacity if set)
        slot = neuron.slots.get(bin_id)
        if slot is None:
            if self.config.max_slots is not None and len(neuron.slots) >= self.config.max_slots:
                # Simplest reuse policy: first existing slot
                slot = next(iter(neuron.slots.values()))
            else:
                slot = Weight()
                neuron.slots[bin_id] = slot
        return slot
