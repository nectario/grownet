class RegionBus:
    def __init__(self):
        self._inhibition_factor = 1.0
        self._modulation_factor = 1.0

    def get_inhibition_factor(self):
        return self._inhibition_factor

    def set_inhibition_factor(self, v):
        self._inhibition_factor = float(v)

    def get_modulation_factor(self):
        return self._modulation_factor

    def set_modulation_factor(self, v):
        self._modulation_factor = float(v)

    def reset(self):
        self._inhibition_factor = 1.0
        self._modulation_factor = 1.0
