# Region metrics (standalone, non-dataclass)
class RegionMetrics:
    def __init__(self) -> None:
        self._delivered_events: int = 0
        self._total_slots: int = 0
        self._total_synapses: int = 0

    # mutators
    def inc_delivered_events(self, n: int = 1) -> None:
        self._delivered_events += int(n)
    def add_slots(self, n: int) -> None:
        self._total_slots += int(n)
    def add_synapses(self, n: int) -> None:
        self._total_synapses += int(n)

    # accessors
    def get_delivered_events(self) -> int: return self._delivered_events
    def get_total_slots(self) -> int:      return self._total_slots
    def get_total_synapses(self) -> int:   return self._total_synapses

    def as_dict(self) -> dict:
        return {"deliveredEvents": self._delivered_events,
                "totalSlots": self._total_slots,
                "totalSynapses": self._total_synapses}
