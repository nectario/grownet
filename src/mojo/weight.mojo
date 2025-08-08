# weight.mojo
# Reinforceable, thresholded unit (used for slots and inter-neuron connections).

from math_utils import smooth_clamp, abs_f64

# Global constants (compile-time)
alias HIT_SATURATION: Int64 = 10_000
alias EPS: Float64  = 0.02   # first-threshold slack (T0)
alias BETA: Float64 = 0.01   # EMA horizon
alias ETA: Float64  = 0.02   # threshold adapt speed
alias R_STAR: Float64 = 0.05 # target firing rate

struct Weight:
    var step_value: Float64 = 0.001
    var strength_value: Float64 = 0.0
    var reinforcement_count: Int64 = 0

    # Adaptive-threshold state (slot-local)
    var threshold_value: Float64 = 0.0
    var ema_rate: Float64 = 0.0
    var first_seen: Bool = False

    fn reinforce(self, modulation_factor: Float64, inhibition_factor: Float64):
        if self.reinforcement_count >= HIT_SATURATION:
            return
        var effective = self.step_value * modulation_factor * inhibition_factor
        self.strength_value = smooth_clamp(self.strength_value + effective, -1.0, 1.0)
        self.reinforcement_count = self.reinforcement_count + 1

    fn update_threshold(self, input_value: Float64) -> Bool:
        # T0: first-time imprint sets a conservative threshold
        if not self.first_seen:
            self.threshold_value = abs_f64(input_value) * (1.0 + EPS)
            self.first_seen = True

        # Fire if gate is higher than the threshold
        var fired = self.strength_value > self.threshold_value

        # T2: homeostasis via EMA towards target rate
        var fired_float: Float64 = 1.0 if fired else 0.0
        self.ema_rate = (1.0 - BETA) * self.ema_rate + BETA * fired_float
        self.threshold_value = self.threshold_value + ETA * (self.ema_rate - R_STAR)

        return fired
