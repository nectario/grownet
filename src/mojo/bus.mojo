struct LateralBus:
    var inhibition_level:  Float64 = 0.0   # 0 .. 1
    var modulation_factor: Float64 = 1.0   # scales learning

    fn decay(self):
        self.inhibition_level  = 0.0
        self.modulation_factor = 1.0
