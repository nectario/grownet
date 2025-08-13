from __future__ import annotations
from typing import Optional, List
from weight import Weight


class SlotPolicyConfig:
    """
    Slot selection & creation policy.

    mode:
        "fixed"            -> single width (slot_width_percent)
        "multi_resolution" -> reuse coarse bins if present, else create at the finest width
        "adaptive"         -> reserved (fields kept for parity; not used by select_or_create_slot yet)
    """
    def __init__(
        self,
        mode: str = "fixed",
        slot_width_percent: float = 0.10,
        multires_widths: Optional[List[float]] = None,   # e.g. [0.10, 0.05, 0.02] (coarse → fine)
        boundary_refine_hits: int = 5,
        target_active_low: int = 6,
        target_active_high: int = 12,
        min_slot_width: float = 0.01,
        max_slot_width: float = 0.20,
        adjust_cooldown_ticks: int = 200,
        adjust_factor_up: float = 1.2,
        adjust_factor_down: float = 0.9,
        nonuniform_schedule: Optional[List[float]] = None
    ) -> None:
        mode_lc = (mode or "fixed").lower()
        if mode_lc not in {"fixed", "multi_resolution", "adaptive"}:
            raise ValueError(f"Unknown mode: {mode}")

        self.mode = mode_lc
        self.slot_width_percent = float(slot_width_percent)
        # default multi-resolution schedule (coarse → fine)
        self.multires_widths = list(multires_widths) if multires_widths is not None else [0.10, 0.05, 0.02]

        # Kept for parity with Java & future adaptive policy
        self.boundary_refine_hits = int(boundary_refine_hits)
        self.target_active_low = int(target_active_low)
        self.target_active_high = int(target_active_high)
        self.min_slot_width = float(min_slot_width)
        self.max_slot_width = float(max_slot_width)
        self.adjust_cooldown_ticks = int(adjust_cooldown_ticks)
        self.adjust_factor_up = float(adjust_factor_up)
        self.adjust_factor_down = float(adjust_factor_down)
        self.nonuniform_schedule = list(nonuniform_schedule) if nonuniform_schedule else None


def compute_percent_delta(last_value: Optional[float], value: float) -> float:
    """
    |Δ| as a percent of the (nonzero) previous value; first stimulus → 0.0.
    """
    if last_value is None or last_value == 0.0:
        return 0.0
    denom = max(1e-9, abs(last_value))
    return 100.0 * abs(value - last_value) / denom


def select_or_create_slot(neuron, value: float, policy: SlotPolicyConfig) -> int:
    """
    Decide the percent‑bucket for this input; create the slot when needed.
    Works for single‑width and multi‑resolution policies.
    Returns the chosen bucket id (int).
    """
    percent = compute_percent_delta(getattr(neuron, "last_input_value", None), value)

    if policy.mode == "multi_resolution" and policy.multires_widths:
        widths = list(policy.multires_widths)
    else:
        widths = [policy.slot_width_percent]

    # Reuse if possible (coarse → fine)
    for width in widths:
        bucket = int(percent // max(1e-9, width))
        if bucket in neuron.slots:
            return bucket

    # Otherwise create at the finest resolution
    finest = widths[-1]
    bucket = int(percent // max(1e-9, finest))
    neuron.slots.setdefault(bucket, Weight())
    return bucket
