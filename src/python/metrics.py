class RegionMetrics:
    def __init__(self):
        # Maintain both snake_case and camelCase fields for cross-language parity
        self.delivered_events = 0
        self.deliveredEvents = 0
        self.total_slots = 0
        self.totalSlots = 0
        self.total_synapses = 0
        self.totalSynapses = 0

    # Helper methods (snake_case; keep aliases in sync)
    def inc_delivered_events(self, by: int = 1):
        inc = int(by)
        self.delivered_events += inc
        self.deliveredEvents += inc

    def add_slots(self, n: int):
        amt = int(n)
        self.total_slots += amt
        self.totalSlots += amt

    def add_synapses(self, n: int):
        amt = int(n)
        self.total_synapses += amt
        self.totalSynapses += amt

    # Optional getters/setters for downstream consumers (set both names)
    def get_deliveredEvents(self):
        return self.deliveredEvents

    def set_deliveredEvents(self, v: int):
        val = int(v)
        self.delivered_events = val
        self.deliveredEvents = val

    def get_totalSlots(self):
        return self.totalSlots

    def set_totalSlots(self, v: int):
        val = int(v)
        self.total_slots = val
        self.totalSlots = val

    def get_totalSynapses(self):
        return self.totalSynapses

    def set_totalSynapses(self, v: int):
        val = int(v)
        self.total_synapses = val
        self.totalSynapses = val
