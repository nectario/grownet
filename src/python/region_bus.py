from dataclasses import dataclass

@dataclass
class RegionBus:
    inhibition_factor: float = 1.0
    modulation_factor: float = 1.0
    current_step: int = 0

    def set_inhibition_factor(self, value: float): self.inhibition_factor = value
    def set_modulation_factor(self, value: float): self.modulation_factor = value
    def tick(self): self.current_step += 1
