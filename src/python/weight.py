from math_utils import smooth_clamp

class Weight:
    """
    One slot (independent threshold sub-unit) with local learning.
    Contains:
      - strength_value: plastic value
      - step_value: learning increment
      - T0+T2 threshold control (threshold_value, ema_rate, seen_first)
      - hit_count / saturation guard
    """
    HIT_SATURATION = 10_000
    EPS = 0.02         # T0 slack
    BETA = 0.01        # EMA horizon
    ETA = 0.02         # Homeostatic speed
    R_TARGET = 0.05    # Desired firing probability

    def __init__(self, step_value: float = 0.001):
        self.step_value = step_value
        self.strength_value = 0.0
        self.hit_count = 0

        # Adaptive threshold state
        self.threshold_value = 0.0
        self.ema_rate = 0.0
        self.seen_first = False

    def reinforce(self, modulation_factor: float = 1.0, inhibition_factor: float = 1.0):
        """Non-linear, ceiling-bounded reinforcement with optional modulation & inhibition."""
        if self.hit_count >= Weight.HIT_SATURATION:
            return
        effective_step = self.step_value * float(modulation_factor)
        self.strength_value = smooth_clamp(self.strength_value + effective_step, -1.0, 1.0)
        # Apply inhibition as a one-tick attenuation
        if inhibition_factor < 1.0:
            self.strength_value *= float(inhibition_factor)
        self.hit_count += 1

    def update_threshold(self, input_value: float) -> bool:
        """T0 imprint + T2 homeostasis. Returns True if this slot fires."""
        if not self.seen_first:
            self.threshold_value = abs(input_value) * (1.0 + Weight.EPS)
            self.seen_first = True

        fired = self.strength_value > self.threshold_value
        self.ema_rate = (1.0 - Weight.BETA) * self.ema_rate + Weight.BETA * (1.0 if fired else 0.0)
        self.threshold_value += Weight.ETA * (self.ema_rate - Weight.R_TARGET)
        return fired
