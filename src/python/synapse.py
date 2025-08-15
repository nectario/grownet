
class Synapse:
    def __init__(self, source, target, feedback=False):
        self.source = source
        self.target = target
        self.feedback = bool(feedback)
        self._strength = 1.0  # placeholder for future use
        self._last_seen_tick = 0

    def getStrengthValue(self): return self._strength
    def setStrengthValue(self, v): self._strength = float(v)
    def getLastSeenTick(self): return self._last_seen_tick
    def setLastSeenTick(self, t): self._last_seen_tick = int(t)
