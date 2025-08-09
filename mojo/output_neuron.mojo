from weight import Weight

struct OutputNeuron:
    var name: String
    var smoothing: Float64 = 0.2
    var slot: Weight = Weight()
    var accumulatedSum: Float64 = 0.0
    var accumulatedCount: Int64 = 0
    var outputValue: Float64 = 0.0

    fn onInput(self, value: Float64, modulationFactor: Float64 = 1.0, inhibitionFactor: Float64 = 1.0) -> Bool:
        self.slot.reinforce(modulationFactor, inhibitionFactor)
        var fired = self.slot.update_threshold(value)
        return fired

    fn onOutput(self, amplitude: Float64):
        self.accumulatedSum = self.accumulatedSum + amplitude
        self.accumulatedCount = self.accumulatedCount + 1

    fn endTick(self):
        if self.accumulatedCount > 0:
            var mean = self.accumulatedSum / Float64(self.accumulatedCount)
            self.outputValue = (1.0 - self.smoothing) * self.outputValue + self.smoothing * mean
        self.accumulatedSum = 0.0
        self.accumulatedCount = 0
