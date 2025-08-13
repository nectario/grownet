alias BETA: Float64          = 0.01      # EMA horizon
alias ADAPT_SPEED: Float64   = 0.02      # threshold adapt speed
alias TARGET_RATE: Float64   = 0.05      # homeostasis target
alias EPSILON_FIRE: Float64  = 0.01      # T0 slack
alias T0_SLACK: Float64      = 0.02
alias HIT_SAT: Int64         = 10_000

fn absf(x: Float64) -> Float64:
    if x < 0.0: return -x
    return x

fn clamp01(x: Float64) -> Float64:
    if x < 0.0: return 0.0
    if x > 1.0: return 1.0
    return x

struct Weight:
    var strength_value: Float64
    var threshold_value: Float64
    var ema_rate: Float64
    var first_seen: Bool
    var hit_count: Int64

    fn __init__() -> Self:
        return Self(0.0, 0.0, 0.0, False, 0)

    fn reinforce(mut self , modulation_factor: Float64, inhibition_factor: Float64):
        if self.hit_count >= HIT_SAT:
            return
        let base_step: Float64 = 0.01
        let step = base_step * modulation_factor * inhibition_factor
        self.strength_value = clamp01(self.strength_value + step)
        self.hit_count += 1

    fn update_threshold(mut self , input_value: Float64) -> Bool:
        # Couple amplitude with strength for an “effective drive”
        let effective = absf(input_value) * (1.0 + self.strength_value)

        if not self.first_seen:
            self.threshold_value = effective * (1.0 - EPSILON_FIRE)
            self.first_seen = True

        let fired = (effective > self.threshold_value)
        self.ema_rate       = (1.0 - BETA) * self.ema_rate + BETA * (1.0 if fired else 0.0)
        self.threshold_value += ADAPT_SPEED * (self.ema_rate - TARGET_RATE)
        return fired
