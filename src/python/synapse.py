
class Synapse:
    def __init__(self, source, target, feedback=False):
        self.source = source
        self.target = target
        self.feedback = bool(feedback)
        self._strength = 1.0  # placeholder for future use
        self.last_seen_tick = 0

    def get_strength_value(self): return self._strength
    def set_strength_value(self, v): self._strength = float(v)
    def get_last_seen_tick(self): return self.last_seen_tick
    def set_last_seen_tick(self, t): self.last_seen_tick = int(t)
