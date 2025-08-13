from dataclasses import dataclass

@dataclass
class LateralBus:
    inhibition_factor: float = 1.0    # < 1.0 means inhibition is active
    modulation_factor: float = 1.0    # scales learning step
    current_step: int = 0

    inhibition_recovery: float = 0.25  # how fast inhibition returns toward 1.0 per tick
    modulation_decay: float = 1.0      # reset multiplier per tick (1.0 -> reset to 1.0)

    def pulse_inhibition(self, factor: float) -> None:
        # Apply the strongest inhibition this tick
        if factor < self.inhibition_factor:
            self.inhibition_factor = factor

    def pulse_modulation(self, factor: float) -> None:
        self.modulation_factor *= factor

    def decay(self) -> None:
        # inhibition recovers toward 1.0
        self.inhibition_factor += (1.0 - self.inhibition_factor) * self.inhibition_recovery
        if self.inhibition_factor > 0.999:
            self.inhibition_factor = 1.0
        # modulation returns toward 1.0 (simple reset here)
        self.modulation_factor = 1.0 if self.modulation_decay >= 1.0 else 1.0 + (self.modulation_factor - 1.0) * self.modulation_decay
        self.current_step += 1
