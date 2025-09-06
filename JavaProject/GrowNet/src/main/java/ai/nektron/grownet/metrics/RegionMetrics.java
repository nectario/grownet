package ai.nektron.grownet.metrics;

/**
 * Lightweight, mutable counters collected during a single tick.
 * Private fields + tiny bump methods keep call sites concise while
 * preserving encapsulation.
 */
public class RegionMetrics {
    private long deliveredEvents;
    private long totalSlots;
    private long totalSynapses;

    // Optional spatial metrics (enabled via Region flag or env var)
    private long   activePixels;
    private double centroidRow;
    private double centroidCol;
    private int    bboxRowMin;
    private int    bboxRowMax;
    private int    bboxColMin;
    private int    bboxColMax;

    public RegionMetrics() {}

    // ---- getters (public read-only surface) ----
    public long getDeliveredEvents() { return deliveredEvents; }
    public long getTotalSlots()      { return totalSlots; }
    public long getTotalSynapses()   { return totalSynapses; }
    public long getActivePixels()    { return activePixels; }
    public double getCentroidRow()   { return centroidRow; }
    public double getCentroidCol()   { return centroidCol; }
    public int getBboxRowMin()       { return bboxRowMin; }
    public int getBboxRowMax()       { return bboxRowMax; }
    public int getBboxColMin()       { return bboxColMin; }
    public int getBboxColMax()       { return bboxColMax; }

    // ---- tiny mutators for internal use ----
    public RegionMetrics incDeliveredEvents()         { deliveredEvents++; return this; }
    public RegionMetrics addDeliveredEvents(long n)   { deliveredEvents += n; return this; }
    public RegionMetrics addSlots(long n)             { totalSlots     += n; return this; }
    public RegionMetrics addSynapses(long n)          { totalSynapses  += n; return this; }

    // optional conveniences
    public RegionMetrics merge(RegionMetrics other) {
        deliveredEvents += other.deliveredEvents;
        totalSlots      += other.totalSlots;
        totalSynapses   += other.totalSynapses;
        activePixels    += other.activePixels;
        // Centroid and bbox do not compose linearly; prefer last
        centroidRow = other.centroidRow;
        centroidCol = other.centroidCol;
        bboxRowMin  = other.bboxRowMin;
        bboxRowMax  = other.bboxRowMax;
        bboxColMin  = other.bboxColMin;
        bboxColMax  = other.bboxColMax;
        return this;
    }

    public RegionMetrics reset() {
        deliveredEvents = totalSlots = totalSynapses = 0L;
        activePixels = 0L;
        centroidRow = centroidCol = 0.0;
        bboxRowMin = 0; bboxRowMax = -1; bboxColMin = 0; bboxColMax = -1;
        return this;
    }

    // ---- spatial setters ----
    public RegionMetrics setActivePixels(long n) { this.activePixels = n; return this; }
    public RegionMetrics setCentroid(double row, double col) { this.centroidRow = row; this.centroidCol = col; return this; }
    public RegionMetrics setBBox(int rowMin, int rowMax, int colMin, int colMax) {
        this.bboxRowMin = rowMin; this.bboxRowMax = rowMax; this.bboxColMin = colMin; this.bboxColMax = colMax; return this;
    }


    @Override public String toString() {
        return "RegionMetrics{" +
                "deliveredEvents=" + deliveredEvents +
                ", totalSlots=" + totalSlots +
                ", totalSynapses=" + totalSynapses +
                ", activePixels=" + activePixels +
                ", centroidRow=" + centroidRow +
                ", centroidCol=" + centroidCol +
                ", bbox=(" + bboxRowMin + "," + bboxRowMax + "," + bboxColMin + "," + bboxColMax + ")" +
                '}';
    }
}
