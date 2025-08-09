from weight import Weight

fn clamp01(x: Float64) -> Float64:
    if x < 0.0: return 0.0
    if x > 1.0: return 1.0
    return x

struct InputNeuron:
    var name: String
    var gain: Float64 = 1.0
    var epsilonFire: Float64 = 0.01
    var slot: Weight = Weight()

    fn onInput(self, value: Float64, modulationFactor: Float64 = 1.0, inhibitionFactor: Float64 = 1.0) -> Bool:
        var effective = clamp01(value * self.gain * modulationFactor * inhibitionFactor)
        if not self.slot.first_seen:
            self.slot.threshold_value = effective * (1.0 - self.epsilonFire)
            self.slot.first_seen = True
        self.slot.strength_value = effective
        # Delegate to threshold logic in Weight
        return self.slot.update_threshold(effective)

    fn onOutput(self, amplitude: Float64):
        # Input neurons do not write; kept for uniform API
        pass
