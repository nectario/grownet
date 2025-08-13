# weight.mojo
# Slot-local state: reinforcement strength + adaptive threshold.
from math_utils import smooth_clamp, abs_val

alias EPS:    F64  = 0.02   # T0 slack (imprint)
alias BETA:   F64  = 0.01   # EMA horizon
alias ETA:    F64  = 0.02   # speed of threshold homeostasis
alias R_STAR: F64  = 0.05   # target firing rate
alias HIT_SATURATION: Int64 = 10_000

struct Weight:
    # Learning parameters
    var step_value:        F64   = 0.001   # reinforcement quantum
    var strength_value:    F64   = 0.0     # synaptic strength (-1..+1)
    var reinforcement_count: Int64 = 0

    # Adaptive threshold state
    var threshold_value:   F64   = 0.0     # dynamic threshold
    var ema_rate:          F64   = 0.0     # recent firing EMA
    var first_seen:        Bool  = False   # T0 imprint guard

    fn reinforce(self, modulation_factor: F64) -> None:
        if self.reinforcement_count >= HIT_SATURATION:
            return
        let effective_step: F64 = self.step_value * modulation_factor
        self.strength_value = smooth_clamp(self.strength_value + effective_step, -1.0, 1.0)
        self.reinforcement_count += 1

    fn update_threshold(self, input_value: F64) -> Bool:
        if not self.first_seen:
            self.threshold_value = abs_val(input_value) * (1.0 + EPS)
            self.first_seen = True

        let fired: Bool = self.strength_value > self.threshold_value

        # EMA of firing (1.0 if fired, else 0.0)
        let fired_f: F64 = 1.0 if fired else 0.0
        self.ema_rate = (1.0 - BETA) * self.ema_rate + BETA * fired_f

        # Homeostatic update towards target rate
        self.threshold_value = self.threshold_value + ETA * (self.ema_rate - R_STAR)
        return fired
