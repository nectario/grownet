# metrics.mojo
# GrowNet: Region metrics (Mojo mirror of Java/C++)

struct RegionMetrics:
    var deliveredEvents: Int64
    var totalSlots: Int64
    var totalSynapses: Int64

    fn __init__() -> Self:
        return Self(deliveredEvents=0, totalSlots=0, totalSynapses=0)

    # getters / setters
    fn getDeliveredEvents(self) -> Int64:
        return self.deliveredEvents

    fn setDeliveredEvents(inout self, value: Int64) -> None:
        self.deliveredEvents = value

    fn getTotalSlots(self) -> Int64:
        return self.totalSlots

    fn setTotalSlots(inout self, value: Int64) -> None:
        self.totalSlots = value

    fn getTotalSynapses(self) -> Int64:
        return self.totalSynapses

    fn setTotalSynapses(inout self, value: Int64) -> None:
        self.totalSynapses = value

    # helpers
    fn incDeliveredEvents(inout self, by: Int64 = 1) -> None:
        self.deliveredEvents += by

    fn addSlots(inout self, count: Int64) -> None:
        self.totalSlots += count

    fn addSynapses(inout self, count: Int64) -> None:
        self.totalSynapses += count
