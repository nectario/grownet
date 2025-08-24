# metrics.mojo
# GrowNet: Region metrics (Mojo mirror of Java/C++)

struct RegionMetrics:
    var deliveredEvents: Int64
    var totalSlots: Int64
    var totalSynapses: Int64

    fn __init__() -> Self:
        return Self(deliveredEvents=0, totalSlots=0, totalSynapses=0)

    # getters / setters
    fn get_delivered_events(self) -> Int64:
        return self.deliveredEvents

    fn set_delivered_events(mut self, value: Int64) -> None:
        self.deliveredEvents = value

    fn get_total_slots(self) -> Int64:
        return self.totalSlots

    fn set_total_slots(mut self, value: Int64) -> None:
        self.totalSlots = value

    fn get_total_synapses(self) -> Int64:
        return self.totalSynapses

    fn set_total_synapses(mut self, value: Int64) -> None:
        self.totalSynapses = value

    # helpers
    fn inc_delivered_events(mut self, by: Int64 = 1) -> None:
        self.deliveredEvents += by

    fn add_slots(mut self, count: Int64) -> None:
        self.totalSlots += count

    fn add_synapses(mut self, count: Int64) -> None:
        self.totalSynapses += count
