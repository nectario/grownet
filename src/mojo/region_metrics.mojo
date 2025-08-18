struct RegionMetrics:
    var delivered_events: Int64
    var total_slots: Int64
    var total_synapses: Int64

    fn __init__(inout self):
        self.delivered_events = 0
        self.total_slots = 0
        self.total_synapses = 0

    fn inc_delivered_events(inout self, amount: Int64 = 1):
        self.delivered_events += amount

    fn add_slots(inout self, amount: Int64):
        self.total_slots += amount

    fn add_synapses(inout self, amount: Int64):
        self.total_synapses += amount
