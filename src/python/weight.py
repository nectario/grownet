from math_utils import clamp, smooth_clamp

class Weight:
    def __init__(self):
        self._strength = 0.0
        self._hit_count = 0
        self._theta = 0.0
        self._ema_rate = 0.0
        self._seen_first = False
        self._last_touched = 0

    # --- getters/setters to mirror other langs ---
    def get_strength_value(self):
        return self._strength

    def set_strength_value(self, v):
        self._strength = clamp(v, -1.0, 1.0)

    def get_threshold_value(self):
        return self._theta

    def set_threshold_value(self, v):
        self._theta = float(v)

    def is_first_seen(self):
        return bool(self._seen_first)

    def set_first_seen(self, flag):
        self._seen_first = bool(flag)

    def get_hit_count(self):
        return self._hit_count

    def set_hit_count(self, v):
        self._hit_count = int(max(0, v))

    def mark_touched(self, tick):
        self._last_touched = int(tick)

    def get_last_touched(self):
        return self._last_touched

    # --- learning helpers ---
    def reinforce(self, modulation_factor):
        # scaled step; keep conservative default
        step = 0.02 * float(modulation_factor)
        if self._hit_count < 10000:
            self._strength = smooth_clamp(self._strength + step, -1.0, 1.0)
            self._hit_count += 1

    def update_threshold(self, input_value, beta=0.05, eta=0.01, r_star=0.1, eps=1e-3):
        # First observation "imprint"
        v = float(input_value)
        if not self._seen_first:
            self._theta = abs(v) * (1.0 + eps)
            self._seen_first = True

        fired = (abs(v) > self._theta) or (self._strength > self._theta)
        # EMA of recent fires (treat True as 1.0, False as 0.0)
        self._ema_rate = (1.0 - beta) * self._ema_rate + beta * (1.0 if fired else 0.0)
        # drift threshold toward target spike rate
        self._theta += eta * (self._ema_rate - r_star)
        return fired
