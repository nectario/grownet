class RegionMetrics:
    def __init__(self):
        # CamelCase fields for DTO parity across languages
        self.delivered_events = 0
        self.total_slots = 0
        self.total_synapses = 0

    # Helper methods (snake_case; call these, not the fields directly)
    def inc_delivered_events(self, by: int = 1):
        self.delivered_events += int(by)

    def add_slots(self, n: int):
        self.total_slots += int(n)

    def add_synapses(self, n: int):
        self.total_synapses += int(n)

    # Optional getters/setters for downstream consumers
    def get_deliveredEvents(self):
        return self.delivered_events

    def set_deliveredEvents(self, v: int):
        self.delivered_events = int(v)

    def get_totalSlots(self):
        return self.total_slots

    def set_totalSlots(self, v: int):
        self.total_slots = int(v)

    def get_totalSynapses(self):
        return self.total_synapses

    def set_totalSynapses(self, v: int):
        self.total_synapses = int(v)
