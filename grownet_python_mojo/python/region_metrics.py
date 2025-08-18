class RegionMetrics:
    """
    Lightweight runtime counters with explicit mutators only (no legacy fields).
    Mirrors the Java/C++ "RegionMetrics" shape but uses snake_case.
    """
    def __init__(self) -> None:
        self._delivered_events: int = 0
        self._total_slots: int = 0
        self._total_synapses: int = 0

    # --------- mutators ---------
    def inc_delivered_events(self, amount: int = 1) -> None:
        self._delivered_events += int(amount)

    def add_slots(self, amount: int) -> None:
        self._total_slots += int(amount)

    def add_synapses(self, amount: int) -> None:
        self._total_synapses += int(amount)

    # --------- accessors ---------
    def get_delivered_events(self) -> int:
        return self._delivered_events

    def get_total_slots(self) -> int:
        return self._total_slots

    def get_total_synapses(self) -> int:
        return self._total_synapses

    def as_dict(self):
        return {
            "delivered_events": self._delivered_events,
            "total_slots": self._total_slots,
            "total_synapses": self._total_synapses,
        }
