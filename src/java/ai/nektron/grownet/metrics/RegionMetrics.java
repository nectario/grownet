package ai.nektron.grownet.metrics;

public class RegionMetrics {
    private long deliveredEvents;
    private long totalSlots;
    private long totalSynapses;

    private long   activePixels;
    private double centroidRow;
    private double centroidCol;
    private int    bboxRowMin;
    private int    bboxRowMax;
    private int    bboxColMin;
    private int    bboxColMax;

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

    public RegionMetrics incDeliveredEvents()         { deliveredEvents++; return this; }
    public RegionMetrics addSlots(long n)             { totalSlots     += n; return this; }
    public RegionMetrics addSynapses(long n)          { totalSynapses  += n; return this; }

    public RegionMetrics setActivePixels(long n) { this.activePixels = n; return this; }
    public RegionMetrics setCentroid(double row, double col) { this.centroidRow = row; this.centroidCol = col; return this; }
    public RegionMetrics setBBox(int rowMin, int rowMax, int colMin, int colMax) {
        this.bboxRowMin = rowMin; this.bboxRowMax = rowMax; this.bboxColMin = colMin; this.bboxColMax = colMax; return this;
    }
}

