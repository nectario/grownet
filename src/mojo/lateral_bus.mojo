# Per-layer shared bus for fast inhibition/modulation events.
struct LateralBus:
    var inhibition_factor: Float64 = 1.0
    var modulation_factor: Float64 = 1.0
    var decay_rate: Float64 = 0.10  # fraction toward neutral each tick
    var current_step: Int64 = 0

    fn set_inhibition_factor(mut self, factor: Float64) -> None:
        self.inhibition_factor = factor

    fn set_modulation_factor(mut self, factor: Float64) -> None:
        self.modulation_factor = factor

    fn decay(mut self) -> None:
        # Move inhibition toward 1.0 (neutral), modulation toward 1.0.
        self.inhibition_factor = 1.0 + (self.inhibition_factor - 1.0) * (1.0 - self.decay_rate)
        self.modulation_factor = 1.0 + (self.modulation_factor - 1.0) * (1.0 - self.decay_rate)
        self.current_step = self.current_step + 1

    fn get_current_step(self) -> Int64:
        return self.current_step

    fn get_step(self) -> Int64:
        return self.current_step
