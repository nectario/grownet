class LateralBus:
    """Per-layer bus carrying transient inhibition and modulation factors."""
    def __init__(self, inhibition_decay: float = 0.9):
        self.inhibition_factor = 0.0   # decays toward 0.0
        self.modulation_factor = 1.0   # resets to 1.0 each tick
        self.inhibition_decay = float(inhibition_decay)
        self.current_step = 0          # increments each tick for cooldowns/metrics

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

    def get_current_step(self) -> int:
        return int(self.current_step)

    # compat alias
    def get_step(self) -> int:
        return self.get_current_step()

    # Mojo‑parity getters (aliases)
    def get_inhibition_factor(self) -> float:
        return float(self.inhibition_factor)

    def get_modulation_factor(self) -> float:
        return float(self.modulation_factor)

    def get_inhibition_decay(self) -> float:
        return float(self.inhibition_decay)

    # Mojo‑parity setters (aliases)
    def set_inhibition(self, factor: float) -> None:
        self.inhibition_factor = float(factor)

    def set_modulation(self, factor: float) -> None:
        self.modulation_factor = float(factor)

    def decay(self, dt: float = 1.0):
        # Optional dt param ignored; preserves behavior; parity shim only
        _ = dt
        # Inhibition decays multiplicatively; modulation resets each tick
        self.inhibition_factor *= self.inhibition_decay
        self.modulation_factor = 1.0
        try:
            self.current_step += 1
        except Exception:
            self.current_step = 0


class RegionBus:
    """Region-wide bus (same policy as LateralBus, region scope)."""
    def __init__(self, inhibition_decay: float = 0.9):
        self.inhibition_factor = 0.0
        self.modulation_factor = 1.0
        self.inhibition_decay = float(inhibition_decay)
        self.current_step = 0

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

    def get_current_step(self) -> int:
        return int(self.current_step)

    def get_step(self) -> int:
        return self.get_current_step()

    def decay(self):
        self.inhibition_factor *= self.inhibition_decay
        self.modulation_factor = 1.0
        try:
            self.current_step += 1
        except Exception:
            self.current_step = 0
