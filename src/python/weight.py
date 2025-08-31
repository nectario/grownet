from math_utils import clamp, smooth_clamp

class Weight:
    def __init__(self):
        self.strength = 0.0
        self.hit_count = 0
        self.theta = 0.0
        self.ema_rate = 0.0
        self.seen_first = False
        self.last_touched = 0

    # --- getters/setters to mirror other langs ---
    def get_strength_value(self):
        return self.strength

    def set_strength_value(self, v):
        self.strength = clamp(v, -1.0, 1.0)

    def get_threshold_value(self):
        return self.theta

    def set_threshold_value(self, v):
        self.theta = float(v)

    def is_first_seen(self):
        return bool(self.seen_first)

    def set_first_seen(self, flag):
        self.seen_first = bool(flag)

    def get_hit_count(self):
        return self.hit_count

    def set_hit_count(self, v):
        self.hit_count = int(max(0, v))

    def mark_touched(self, tick):
        self.last_touched = int(tick)

    def get_last_touched(self):
        return self.last_touched

    # --- learning helpers ---
    def reinforce(self, modulation_factor):
        # scaled step; keep conservative default
        step = 0.02 * float(modulation_factor)
        if self.hit_count < 10000:
            self.strength = smooth_clamp(self.strength + step, -1.0, 1.0)
            self.hit_count += 1

    def update_threshold(self, input_value, beta=0.05, eta=0.01, r_star=0.1, eps=1e-3):
        # First observation "imprint"
        value_float = float(input_value)
        if not self.seen_first:
            self.theta = abs(value_float) * (1.0 + eps)
            self.seen_first = True

        fired = (abs(value_float) > self.theta) or (self.strength > self.theta)
        # EMA of recent fires (treat True as 1.0, False as 0.0)
        self.ema_rate = (1.0 - beta) * self.ema_rate + beta * (1.0 if fired else 0.0)
        # drift threshold toward target spike rate
        self.theta += eta * (self.ema_rate - r_star)
        return fired
