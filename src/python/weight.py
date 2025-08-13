from dataclasses import dataclass
from math_utils import smooth_clamp


@dataclass
class Weight:
    # learning
    step_value: float = 0.001
    strength_value: float = 0.0
    hit_count: int = 0

    # adaptive threshold (T0 + T2)
    threshold_value: float = 0.0
    ema_rate: float = 0.0
    seen_first: bool = False

    # constants (can be tuned at runtime if you prefer)
    HIT_SATURATION: int = 10_000
    EPS: float = 0.02     # T0 slack
    BETA: float = 0.01    # EMA horizon
    ETA: float = 0.02     # adaptation speed
    R_STAR: float = 0.05  # target firing-rate

    def reinforce(self, modulation_factor: float = 1.0, inhibition_factor: float = 0.0) -> None:
        """Non-linear, ceiling-bounded reinforcement."""
        if self.hit_count >= self.HIT_SATURATION:
            return
        effective_step = self.step_value * modulation_factor
        self.strength_value = smooth_clamp(self.strength_value + effective_step, -1.0, 1.0)
        self.hit_count += 1

    def update_threshold(self, input_value: float) -> bool:
        """Hybrid T0 imprint + T2 homeostasis; returns True if 'fired'."""
        if not self.seen_first:
            self.threshold_value = abs(input_value) * (1.0 + self.EPS)
            self.seen_first = True

        fired = self.strength_value > self.threshold_value

        fired_float = 1.0 if fired else 0.0
        self.ema_rate = (1.0 - self.BETA) * self.ema_rate + self.BETA * fired_float
        self.threshold_value += self.ETA * (self.ema_rate - self.R_STAR)
        return fired
