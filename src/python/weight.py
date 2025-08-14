from __future__ import annotations
from dataclasses import dataclass
from math_utils import smooth_clamp

@dataclass
class Weight:
    # Learning parameters
    step_value: float = 0.001
    strength_value: float = 0.0
    reinforcement_count: int = 0

    # Adaptive threshold state (hybrid T0+T2)
    threshold_value: float = 0.0
    ema_rate: float = 0.0
    first_seen: bool = False

    # Constants (can be exposed via config if needed)
    HIT_SATURATION: int = 10_000
    EPS: float = 0.02
    BETA: float = 0.01
    ETA: float = 0.02
    R_STAR: float = 0.05

    def reinforce(self, modulation_factor: float, inhibition_factor: float) -> None:
        if self.reinforcement_count >= self.HIT_SATURATION:
            return
        effective_step = self.step_value * modulation_factor
        self.strength_value = smooth_clamp(self.strength_value + effective_step, -1.0, 1.0)
        # simple multiplicative inhibition on the edge
        if inhibition_factor > 0.0:
            self.strength_value *= (1.0 - inhibition_factor)
        self.reinforcement_count += 1

    def update_threshold(self, input_value: float) -> bool:
        if not self.first_seen:
            self.threshold_value = abs(input_value) * (1.0 + self.EPS)
            self.first_seen = True
        fired = self.strength_value > self.threshold_value
        self.ema_rate = (1.0 - self.BETA) * self.ema_rate + self.BETA * (1.0 if fired else 0.0)
        self.threshold_value += self.ETA * (self.ema_rate - self.R_STAR)
        return fired
