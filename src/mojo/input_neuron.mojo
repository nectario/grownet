from weight import Weight

fn clamp01(x: Float64) -> Float64:
    if x < 0.0: return 0.0
    if x > 1.0: return 1.0
    return x

struct InputNeuron:
    var name: String
    var gain: Float64 = 1.0
    var epsilon_fire: Float64 = 0.01
    var slot: Weight = Weight()

    fn on_sensor_value(self, value: Float64, modulation: Float64 = 1.0, inhibition: Float64 = 1.0) -> Bool:
        var effective = clamp01(value * self.gain * modulation * inhibition)
        if not self.slot.first_seen:
            self.slot.threshold_value = effective * (1.0 - self.epsilon_fire)
            self.slot.first_seen = True
        self.slot.strength_value = effective
        return self.slot.update_threshold(effective)
