# bus.mojo — lateral events between neurons/layers
struct LateralBus:
    var inhibition_factor: F64 = 0.0   # 0 … 1 (0 = none)
    var modulation_factor: F64 = 1.0   # scales learning rate

    fn decay(self) -> None:
        self.inhibition_factor = 0.0
        self.modulation_factor = 1.0
