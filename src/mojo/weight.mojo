# weight.mojo — slot state: strength + adaptive threshold

from math_utils import smooth_clamp, abs_val

struct Weight:
    # learning
    var step_value:        F64  = 0.001
    var strength_value:    F64  = 0.0
    var reinforcement_count: Int64 = 0

    # adaptive-threshold
    var threshold_value:   F64 = 0.0
    var ema_rate:          F64 = 0.0
    var first_seen:        Bool = False

    # knobs (kept local for simplicity; can be injected later)
    alias HIT_SATURATION:  Int64 = 10_000
    alias EPS:             F64 = 0.02
    alias BETA:            F64 = 0.01
    alias ETA:             F64 = 0.02
    alias R_STAR:          F64 = 0.05

    fn reinforce(self, modulation: F64) -> None:
        if self.reinforcement_count >= self.HIT_SATURATION:
            return
        let step = self.step_value * modulation
        self.strength_value = smooth_clamp(self.strength_value + step, -1.0, 1.0)
        self.reinforcement_count = self.reinforcement_count + 1

    fn update_threshold(self, input_value: F64) -> Bool:
        if not self.first_seen:
            self.threshold_value = abs_val(input_value) * (1.0 + self.EPS)
            self.first_seen = True

        let fired = self.strength_value > self.threshold_value
        let fired_f = 1.0 if fired else 0.0

        self.ema_rate = (1.0 - self.BETA) * self.ema_rate + self.BETA * fired_f
        self.threshold_value = self.threshold_value + self.ETA * (self.ema_rate - self.R_STAR)
        return fired
