from math_utils import MathUtils

struct Weight:
    var strength: Float64 = 0.0
    var hit_count: Int = 0
    # Adaptive-threshold state
    var theta: Float64 = 0.0
    var ema_rate: Float64 = 0.0
    var seen_first: Bool = False
    # Frozen-slot support (opt-in)
    var frozen: Bool = False

    # Learning hyper-params (kept local for stability)
    var step_val: Float64 = 0.01
    var ema_beta: Float64 = 0.10
    var eta: Float64 = 0.005
    var r_star: Float64 = 0.02
    var epsilon_fire: Float64 = 0.01

    fn reinforce(mut self, modulation_factor: Float64) -> None:
        if self.frozen:
            return
        if self.hit_count >= 10000:
            return
        var effective = self.step_val * modulation_factor
        self.strength = MathUtils.smooth_clamp(self.strength + effective, -1.0, 1.0)
        self.hit_count += 1

    fn update_threshold(mut self, input_value: Float64) -> Bool:
        if self.frozen:
            var v = input_value
            return (MathUtils.abs_f64(v) > self.theta) or (self.strength > self.theta)
        # T0: imprint
        if not self.seen_first:
            var mag = MathUtils.abs_f64(input_value)
            self.theta = mag * (1.0 + self.epsilon_fire)
            self.seen_first = True
        # Fire decision
        var fired = self.strength > self.theta
        # EMA + adaptive theta
        self.ema_rate = (1.0 - self.ema_beta) * self.ema_rate + self.ema_beta * (1.0 if fired else 0.0)
        self.theta = self.theta + self.eta * (self.ema_rate - self.r_star)
        return fired

    fn freeze(mut self) -> None:
        self.frozen = True

    fn unfreeze(mut self) -> None:
        self.frozen = False

    fn is_frozen(self) -> Bool:
        return self.frozen
