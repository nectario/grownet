class LateralBus:
    """Per-layer bus for inhibition/modulation."""
    def __init__(self, inhibition_decay: float = 0.9):
        self.inhibition_factor = 0.0   # decays toward 0.0
        self.modulation_factor = 1.0   # resets to 1.0 each tick
        self.inhibition_decay = float(inhibition_decay)

    # setters
    def set_inhibition(self, factor: float):
        self.inhibition_factor = float(factor)
    # compat alias
    def set_inhibition_factor(self, factor: float):
        self.set_inhibition(factor)

    def set_modulation(self, factor: float):
        self.modulation_factor = float(factor)
    # compat alias
    def set_modulation_factor(self, factor: float):
        self.set_modulation(factor)

    # getters
    def get_inhibition_factor(self) -> float:
        return float(self.inhibition_factor)

    def get_modulation_factor(self) -> float:
        return float(self.modulation_factor)

    def get_inhibition_decay(self) -> float:
        return float(self.inhibition_decay)

    def decay(self):
        # Inhibition decays multiplicatively; modulation resets each tick
        self.inhibition_factor *= self.inhibition_decay
        self.modulation_factor = 1.0


class RegionBus:
    """Region-wide bus (same policy as LateralBus, region scope)."""
    def __init__(self, inhibition_decay: float = 0.9):
        self.inhibition_factor = 0.0
        self.modulation_factor = 1.0
        self.inhibition_decay = float(inhibition_decay)

    # setters (canonical + compat aliases)
    def set_inhibition(self, factor: float):
        self.inhibition_factor = float(factor)
    def set_inhibition_factor(self, factor: float):
        self.set_inhibition(factor)

    def set_modulation(self, factor: float):
        self.modulation_factor = float(factor)
    def set_modulation_factor(self, factor: float):
        self.set_modulation(factor)

    # getters
    def get_inhibition_factor(self) -> float:
        return float(self.inhibition_factor)

    def get_modulation_factor(self) -> float:
        return float(self.modulation_factor)

    def get_inhibition_decay(self) -> float:
        return float(self.inhibition_decay)

    def decay(self):
        self.inhibition_factor *= self.inhibition_decay
        self.modulation_factor = 1.0
