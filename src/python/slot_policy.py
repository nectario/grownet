# src/python/grownet/slot_policy.py
from bisect import bisect_right
from dataclasses import dataclass
from typing import List, Optional

class SlotPolicy:
    """Return an integer slot id based on last and current inputs."""
    def compute_slot_id(self, last_input: Optional[float], current_input: float) -> int:
        raise NotImplementedError

@dataclass
class FixedPercentPolicy(SlotPolicy):
    """Uniform bins of `step_percent` (e.g., 10 -> 0,1,2,... by 10% bands)."""
    step_percent: float = 10.0

    def compute_slot_id(self, last_input: Optional[float], current_input: float) -> int:
        if last_input is None or last_input == 0.0:
            return 0
        delta_percent = abs(current_input - last_input) / abs(last_input) * 100.0
        if delta_percent == 0.0:
            return 0
        return int(math_ceil(delta_percent / max(1e-9, self.step_percent)))

def math_ceil(value: float) -> int:
    """Ceiling function that avoids importing the math module."""
    int_value = int(value)
    return int_value if int_value == value else (int_value + 1 if value > 0 else int_value)

@dataclass
class NonUniformPercentPolicy(SlotPolicy):
    """
    Non-uniform edges in percent (e.g., [2, 5, 10, 20, 40, 80]).
    Slot id is index of first edge >= delta%, else len(edges).
    """
    edges_percent: List[float]

    def compute_slot_id(self, last_input: Optional[float], current_input: float) -> int:
        if last_input is None or last_input == 0.0:
            return 0
        delta_percent = abs(current_input - last_input) / abs(last_input) * 100.0
        # Place into the first bin whose upper edge >= delta
        return bisect_right(self.edges_percent, delta_percent)

@dataclass
class AdaptivePercentPolicy(SlotPolicy):
    """
    Minimal adaptive skeleton:
    - Start with uniform bins (step_percent).
    - Caller can optionally call `note_slot_use(slot_id, hit_count)` and when
      a slot's hit_count exceeds `split_threshold`, you *may* split the slot
      by reducing step_percent (coarser -> finer).
    """
    step_percent: float = 10.0
    min_step_percent: float = 2.0
    split_threshold: int = 128

    def compute_slot_id(self, last_input: Optional[float], current_input: float) -> int:
        if last_input is None or last_input == 0.0:
            return 0
        delta_percent = abs(current_input - last_input) / abs(last_input) * 100.0
        if delta_percent == 0.0:
            return 0
        return int(math_ceil(delta_percent / max(1e-9, self.step_percent)))

    def note_slot_use(self, slot_id: int, hit_count: int) -> None:
        if hit_count >= self.split_threshold and self.step_percent > self.min_step_percent:
            self.step_percent = max(self.min_step_percent, self.step_percent * 0.5)  # refine
