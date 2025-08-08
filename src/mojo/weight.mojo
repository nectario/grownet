import math_utils

# ------------------------------------------------------------------

struct Weight:
    # learning parameters
    var step_value:       Float64 = 0.001
    var strength_value:   Float64 = 0.0
    var reinforcement_cnt:Int64   = 0

    # adaptive threshold
    var threshold_value: Float64 = 0.0
    var ema_rate:        Float64 = 0.0
    var first_seen:      Bool    = false

    alias HIT_SATURATION = 10_000
    alias EPS = 0.02
    alias BETA = 0.01
    alias ETA = 0.02
    alias TARGET_RATE = 0.05

    fn reinforce(self, modulation: F64):
        if self.reinforcement_cnt >= Weight.HIT_SATURATION:
            return
        var effective = self.step_value * modulation
        self.strength_value = math_utils.smooth_clamp(
            self.strength_value + effective, -1.0, 1.0)
        self.reinforcement_cnt += 1

    fn update_threshold(self, input_val: Float64) -> Bool:
        if not self.first_seen:
            self.threshold_value = abs(input_val) * (1.0 + EPS)
            self.first_seen = true

        var fired = self.strength_value > self.threshold_value
        var fired_f64: Float64 = 1.0 if fired else 0.0

        self.ema_rate       = (1.0 - BETA) * self.ema_rate + BETA * fired_f64
        self.threshold_value += ETA * (self.ema_rate - TARGET_RATE)
        return fired
