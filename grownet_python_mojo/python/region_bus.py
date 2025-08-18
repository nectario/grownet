class RegionBus:
    """
    Simple "bus" for region‑wide signals (inhibition, modulation).  Intentionally minimal.
    """
    def __init__(self) -> None:
        self._inhibition: float = 0.0
        self._modulation: float = 0.0
        self._decay: float = 0.1  # simple decay factor applied at end_tick

    def set_inhibition_factor(self, v: float) -> None:
        self._inhibition = float(v)

    def set_modulation_factor(self, v: float) -> None:
        self._modulation = float(v)

    def get_inhibition_factor(self) -> float:
        return self._inhibition

    def get_modulation_factor(self) -> float:
        return self._modulation

    def end_tick(self) -> None:
        # simple exponential decay toward zero
        self._inhibition *= (1.0 - self._decay)
        self._modulation *= (1.0 - self._decay)
