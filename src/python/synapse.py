
class Synapse:
    def __init__(self, source, target, feedback=False):
        self.source = source
        self.target = target
        self.feedback = bool(feedback)
        self.strength = 1.0  # placeholder for future use
        self.last_seen_tick = 0

    # snake_case accessors only (no camelCase)
    def get_strength_value(self):
        return self.strength

    def set_strength_value(self, v):
        self.strength = float(v)

    def get_last_seen_tick(self):
        return self.last_seen_tick

    def set_last_seen_tick(self, t):
        self.last_seen_tick = int(t)
