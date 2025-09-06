# metrics.mojo
# GrowNet: Region metrics (Mojo mirror of Python snake_case)

struct RegionMetrics:
    var delivered_events: Int64
    var total_slots: Int64
    var total_synapses: Int64
    # Optional spatial metrics
    var active_pixels: Int64
    var centroid_row: Float64
    var centroid_col: Float64
    var bbox: tuple[Int, Int, Int, Int]

    fn __init__() -> Self:
        return Self(
            delivered_events=0,
            total_slots=0,
            total_synapses=0,
            active_pixels=0,
            centroid_row=0.0,
            centroid_col=0.0,
            bbox=(0, -1, 0, -1)
        )

    # helpers
    fn inc_delivered_events(mut self, amount: Int64 = 1) -> None:
        self.delivered_events = self.delivered_events + amount

    fn add_slots(mut self, count: Int64) -> None:
        self.total_slots = self.total_slots + count

    fn add_synapses(mut self, count: Int64) -> None:
        self.total_synapses = self.total_synapses + count

    fn set_bbox(mut self, row_min: Int, row_max: Int, col_min: Int, col_max: Int) -> None:
        self.bbox = (row_min, row_max, col_min, col_max)
