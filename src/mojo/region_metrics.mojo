------------------------------
# GrowNet RegionMetrics (Mojo)
# Snake_case API, mirror of Python version
# ------------------------------
struct RegionMetrics:
    var delivered_events: Int64
    var total_slots: Int64
    var total_synapses: Int64

    fn __init__(mut self):
        self.delivered_events = 0
        self.total_slots = 0
        self.total_synapses = 0

    # --- mutators ---
    fn inc_delivered_events(mut self, n: Int64 = 1):
        self.delivered_events += n

    fn add_slots(mut self, n: Int64):
        self.total_slots += n

    fn add_synapses(mut self, n: Int64):
        self.total_synapses += n

    # --- accessors ---
    fn get_delivered_events(self) -> Int64:
        return self.delivered_events

    fn get_total_slots(self) -> Int64:
        return self.total_slots

    fn get_total_synapses(self) -> Int64:
        return self.total_synapses
