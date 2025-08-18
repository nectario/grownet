struct RegionBus:
    var inhibition: Float64
    var modulation: Float64
    var decay: Float64

    fn __init__(inout self):
        self.inhibition = 0.0
        self.modulation = 0.0
        self.decay = 0.1

    fn set_inhibition_factor(inout self, v: Float64):
        self.inhibition = v

    fn set_modulation_factor(inout self, v: Float64):
        self.modulation = v

    fn get_inhibition_factor(self) -> Float64:
        return self.inhibition

    fn get_modulation_factor(self) -> Float64:
        return self.modulation

    fn end_tick(inout self):
        self.inhibition *= (1.0 - self.decay)
        self.modulation *= (1.0 - self.decay)
