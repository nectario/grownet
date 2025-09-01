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

    public RegionMetrics() {}

    // ---- getters (public read-only surface) ----
    public long getDeliveredEvents() { return deliveredEvents; }
    public long getTotalSlots()      { return totalSlots; }
    public long getTotalSynapses()   { return totalSynapses; }

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
        return this;
    }

    public RegionMetrics reset() {
        deliveredEvents = totalSlots = totalSynapses = 0L;
        return this;
    }


    @Override public String toString() {
        return "RegionMetrics{" +
                "deliveredEvents=" + deliveredEvents +
                ", totalSlots=" + totalSlots +
                ", totalSynapses=" + totalSynapses + '}';
    }
}