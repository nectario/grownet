class RegionMetrics:
    def __init__(self):
        # Snake_case fields only (no camelCase)
        self.delivered_events = 0
        self.total_slots = 0
        self.total_synapses = 0

        # Optional spatial metrics (off unless enabled by Region/env)
        self.active_pixels = 0
        self.centroid_row = 0.0
        self.centroid_col = 0.0
        # bbox stored both as a tuple and split fields for parity
        self.bbox = (0, -1, 0, -1)

    # Helper methods (snake_case; keep aliases in sync)
    def inc_delivered_events(self, by: int = 1):
        inc = int(by)
        self.delivered_events += inc

    def add_slots(self, n: int):
        amt = int(n)
        self.total_slots += amt

    def add_synapses(self, n: int):
        amt = int(n)
        self.total_synapses += amt
    def set_bbox(self, row_min: int, row_max: int, col_min: int, col_max: int):
        self.bbox = (int(row_min), int(row_max), int(col_min), int(col_max))

    # Mojo-parity getters (aliases)
    def get_delivered_events(self) -> int:
        return int(self.delivered_events)

    def get_total_slots(self) -> int:
        return int(self.total_slots)

    def get_total_synapses(self) -> int:
        return int(self.total_synapses)
