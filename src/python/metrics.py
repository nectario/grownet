# metrics.py
# GrowNet: Region metrics (Python mirror of Java/C++)
# NOTE: Keep method names camelCase to match Java/C++ for now.

class RegionMetrics:
    def __init__(self):
        self.deliveredEvents = 0
        self.total_slots = 0
        self.total_synapses = 0

    # --------------- getters / setters ---------------
    def get_deliveredEvents(self) -> int:
        return self.deliveredEvents

    def set_eliveredEvents(self, value: int) -> None:
        self.deliveredEvents = int(value)

    def get_total_slots(self) -> int:
        return self.total_slots

    def set_total_slots(self, value: int) -> None:
        self.total_slots = int(value)

    def get_total_synapses(self) -> int:
        return self.total_synapses

    def set_total_synapses(self, value: int) -> None:
        self.total_synapses = int(value)

    # --------------- helpers ---------------
    def inc_delivered_events(self, by: int = 1) -> None:
        self.deliveredEvents += int(by)

    def add_slots(self, count: int) -> None:
        self.total_slots += int(count)

    def add_synapses(self, count: int) -> None:
        self.total_synapses += int(count)

    # Optional: repr for debugging
    def __repr__(self) -> str:
        return f"RegionMetrics(deliveredEvents={self.deliveredEvents}, totalSlots={self.total_slots}, totalSynapses={self.total_synapses})"
