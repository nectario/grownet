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

    # Python/Mojo-parity getters
    fn get_inhibition_factor(self) -> Float64:
        return self.inhibition_factor

    fn get_modulation_factor(self) -> Float64:
        return self.modulation_factor

    fn get_inhibition_decay(self) -> Float64:
        return self.decay_rate

    # Python-parity setter aliases
    fn set_inhibition(mut self, factor: Float64) -> None:
        self.inhibition_factor = factor

    fn set_modulation(mut self, factor: Float64) -> None:
        self.modulation_factor = factor

    fn set_inhibition_decay(mut self, value: Float64) -> None:
        self.decay_rate = value

    fn decay(mut self) -> None:
        # Multiplicative inhibition decay; modulation reset; step++ (Python/Java parity)
        self.inhibition_factor = self.inhibition_factor * self.decay_rate
        self.modulation_factor = 1.0
        self.current_step = self.current_step + 1

    # Optional arity convenience (ignored dt, preserves parity without behavior change)
    fn decay(mut self, dt: Float64) -> None:
        _ = dt
        self.inhibition_factor = self.inhibition_factor * self.decay_rate
        self.modulation_factor = 1.0
        self.current_step = self.current_step + 1

    fn get_current_step(self) -> Int64:
        return self.current_step

    fn get_step(self) -> Int64:
        return self.current_step
