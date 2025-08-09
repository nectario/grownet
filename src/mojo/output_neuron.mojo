from weight import Weight

struct OutputNeuron:
    var name: String
    var smoothing: Float64 = 0.2
    var slot: Weight = Weight()
    var accumulated_sum: Float64 = 0.0
    var accumulated_count: Int64 = 0
    var output_value: Float64 = 0.0

    fn on_routed_event(self, value: Float64, modulation: Float64 = 1.0, inhibition: Float64 = 1.0) -> Bool:
        self.slot.reinforce(modulation, inhibition)
        var fired = self.slot.update_threshold(value)
        if fired:
            self.accumulated_sum = self.accumulated_sum + value
            self.accumulated_count = self.accumulated_count + 1
        return fired

    fn end_tick(self):
        if self.accumulated_count > 0:
            var mean = self.accumulated_sum / Float64(self.accumulated_count)
            self.output_value = (1.0 - self.smoothing) * self.output_value + self.smoothing * mean
        self.accumulated_sum = 0.0
        self.accumulated_count = 0
