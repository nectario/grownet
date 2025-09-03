
struct RegionMetrics:
    var delivered_events: Int
    var total_slots: Int
    var total_synapses: Int

    fn __init__(mut self):
        self.delivered_events = 0
        self.total_slots = 0
        self.total_synapses = 0

    # --- getters ---
    fn get_delivered_events(self) -> Int:
        return self.delivered_events

    fn get_total_slots(self) -> Int:
        return self.total_slots

    fn get_total_synapses(self) -> Int:
        return self.total_synapses

    # --- mutators/accumulators ---
    fn inc_delivered_events(mut self, amount: Int = 1) -> None:
        self.delivered_events += amount

    fn add_slots(mut self, count: Int) -> None:
        self.total_slots += count

    fn add_synapses(mut self, count: Int) -> None:
        self.total_synapses += count
