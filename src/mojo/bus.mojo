# bus.mojo
# Lateral inhibition / global neuromodulation bus (per layer / region).

struct LateralBus:
    var inhibition_factor: F64 = 0.0   # 0..1
    var modulation_factor: F64 = 1.0   # scales learning rate
    var current_step: Int64 = 0

    fn decay(self) -> None:
        # Reset transient signals and advance time.
        self.inhibition_factor = 0.0
        self.modulation_factor = 1.0
        self.current_step += 1

    fn set_inhibition(self, value: F64) -> None:
        self.inhibition_factor = value

    fn set_modulation(self, value: F64) -> None:
        self.modulation_factor = value
