# Per-layer shared bus for fast inhibition/modulation events.
struct LateralBus:
    var inhibition_factor: Float64 = 1.0
    var modulation_factor: Float64 = 1.0
    var decay_rate: Float64 = 0.90  # multiplicative inhibition decay per tick
    var current_step: Int64 = 0

    fn set_inhibition_factor(mut self, factor: Float64) -> None:
        self.inhibition_factor = factor

    fn set_modulation_factor(mut self, factor: Float64) -> None:
        self.modulation_factor = factor

    fn decay(mut self) -> None:
        # Multiplicative inhibition decay; modulation reset; step++ (Python/Java parity)
        self.inhibition_factor = self.inhibition_factor * self.decay_rate
        self.modulation_factor = 1.0
        self.current_step = self.current_step + 1

    fn get_current_step(self) -> Int64:
        return self.current_step

    fn get_step(self) -> Int64:
        return self.current_step
