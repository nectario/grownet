
class LateralBus:
    def __init__(self):
        self._inhibition_factor = 0.0  # decays toward 0 each tick
        self._modulation_factor = 1.0  # resets to 1.0 each tick

    # getters / setters
    def getInhibitionFactor(self): return self._inhibition_factor
    def get_inhibition_factor(self): return self._inhibition_factor
    def setInhibitionFactor(self, v): self._inhibition_factor = float(v)
    def set_inhibition_factor(self, v): self._inhibition_factor = float(v)

    def getModulationFactor(self): return self._modulation_factor
    def get_modulation_factor(self): return self._modulation_factor
    def setModulationFactor(self, v): self._modulation_factor = float(v)
    def set_modulation_factor(self, v): self._modulation_factor = float(v)

    def decay(self):
        # inhibition decays, modulation resets
        self._inhibition_factor *= 0.85
        self._modulation_factor = 1.0


class RegionBus:
    def __init__(self):
        self._inhibition_factor = 0.0
        self._modulation_factor = 1.0

    def getInhibitionFactor(self): return self._inhibition_factor
    def setInhibitionFactor(self, v): self._inhibition_factor = float(v)
    def getModulationFactor(self): return self._modulation_factor
    def setModulationFactor(self, v): self._modulation_factor = float(v)

    # aliases
    get_inhibition_factor = getInhibitionFactor
    set_inhibition_factor = setInhibitionFactor
    get_modulation_factor = getModulationFactor
    set_modulation_factor = setModulationFactor
