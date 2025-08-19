class RegionMetrics:
    def __init__(self):
        # CamelCase fields for DTO parity across languages
        self.deliveredEvents = 0
        self.totalSlots = 0
        self.totalSynapses = 0

    # Helper methods (snake_case; call these, not the fields directly)
    def inc_delivered_events(self, by: int = 1):
        self.deliveredEvents += int(by)

    def add_slots(self, n: int):
        self.totalSlots += int(n)

    def add_synapses(self, n: int):
        self.totalSynapses += int(n)

    # Optional getters/setters for downstream consumers
    def get_deliveredEvents(self):
        return self.deliveredEvents

    def set_deliveredEvents(self, v: int):
        self.deliveredEvents = int(v)

    def get_totalSlots(self):
        return self.totalSlots

    def set_totalSlots(self, v: int):
        self.totalSlots = int(v)

    def get_totalSynapses(self):
        return self.totalSynapses

    def set_totalSynapses(self, v: int):
        self.totalSynapses = int(v)
