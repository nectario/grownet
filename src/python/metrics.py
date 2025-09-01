class RegionMetrics:
    def __init__(self):
        # Maintain both snake_case and camelCase fields for cross-language parity
        self.delivered_events = 0
        self.deliveredEvents = 0
        self.total_slots = 0
        self.totalSlots = 0
        self.total_synapses = 0
        self.totalSynapses = 0

        # Optional spatial metrics (off unless enabled by Region/env)
        self.active_pixels = 0
        self.activePixels = 0
        self.centroid_row = 0.0
        self.centroidRow = 0.0
        self.centroid_col = 0.0
        self.centroidCol = 0.0
        # bbox stored both as a tuple and split fields for parity
        self.bbox = (0, -1, 0, -1)
        self.bboxRowMin = 0
        self.bboxRowMax = -1
        self.bboxColMin = 0
        self.bboxColMax = -1

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

    # Spatial getters/setters (keep snake+camel in sync)
    def set_activePixels(self, v: int):
        val = int(v)
        self.active_pixels = val
        self.activePixels = val

    def set_centroidRow(self, v: float):
        val = float(v)
        self.centroid_row = val
        self.centroidRow = val

    def set_centroidCol(self, v: float):
        val = float(v)
        self.centroid_col = val
        self.centroidCol = val

    def set_bbox(self, row_min: int, row_max: int, col_min: int, col_max: int):
        self.bbox = (int(row_min), int(row_max), int(col_min), int(col_max))
        self.bboxRowMin, self.bboxRowMax, self.bboxColMin, self.bboxColMax = self.bbox
