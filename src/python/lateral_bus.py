class LateralBus:
    def __init__(self):
        self._inhibition_factor = 1.0  # multiplicative (<=1 reduces)
        self._modulation_factor = 1.0  # scales learning (+/-)

    def get_inhibition_factor(self):
        return self._inhibition_factor

    def set_inhibition_factor(self, v):
        self._inhibition_factor = float(v)

    def get_modulation_factor(self):
        return self._modulation_factor

    def set_modulation_factor(self, v):
        self._modulation_factor = float(v)

    def decay(self, alpha=0.5):
        # move both factors halfway to neutral each tick
        self._inhibition_factor = 1.0 + alpha * (self._inhibition_factor - 1.0)
        self._modulation_factor = 1.0 + alpha * (self._modulation_factor - 1.0)
