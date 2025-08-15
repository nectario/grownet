# Region-wide pulse bus (used by Region to broadcast single-tick pulses).
struct RegionBus:
    var inhibition_factor: Float64 = 1.0
    var modulation_factor: Float64 = 1.0

    fn set_inhibition_factor(inout self, factor: Float64) -> None:
        self.inhibition_factor = factor

    fn set_modulation_factor(inout self, factor: Float64) -> None:
        self.modulation_factor = factor

    fn reset(inout self) -> None:
        self.inhibition_factor = 1.0
        self.modulation_factor = 1.0
