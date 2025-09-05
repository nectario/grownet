package ai.nektron.grownet.growth;

/**
 * Conservative growth policy with simple knobs and internal cooldowns.
 *
 * Defaults aim to be safe (no growth unless pressure is clearly present).
 */
public final class GrowthPolicy {

    // ---------------- layer growth ----------------
    private boolean enableLayerGrowth = false;
    private int     maxLayers         = 8;      // hard cap
    private double  avgSlotsThreshold = 24.0;   // grow if avg slots/neuron >= threshold
    private long    layerCooldownTicks = 500;   // wait between layer additions
    // Optional OR trigger: grow if percent of neurons at capacity & using fallback exceeds this
    private double  percentAtCapFallbackThreshold = 0.0; // 0 disables OR-trigger

    // ---------------- neuron growth (best‑effort) ----------------
    private boolean enableNeuronGrowth = false;
    private double  neuronOutlierThresholdPct = 60.0; // temporal‑focus delta% vs anchor
    private long    neuronCooldownTicks = 200;

    // ---------------- internal cooldown state ----------------
    private long lastLayerGrowthTick  = Long.MIN_VALUE / 4;
    private long lastNeuronGrowthTick = Long.MIN_VALUE / 4;

    // ---------------- accessors ----------------
    public boolean isEnableLayerGrowth() { return enableLayerGrowth; }
    public GrowthPolicy setEnableLayerGrowth(boolean v) { this.enableLayerGrowth = v; return this; }

    public int getMaxLayers() { return Math.max(1, maxLayers); }
    public GrowthPolicy setMaxLayers(int v) { this.maxLayers = Math.max(1, v); return this; }

    public double getAvgSlotsThreshold() { return Math.max(0.0, avgSlotsThreshold); }
    public GrowthPolicy setAvgSlotsThreshold(double v) { this.avgSlotsThreshold = Math.max(0.0, v); return this; }

    public double getPercentAtCapFallbackThreshold() { return Math.max(0.0, percentAtCapFallbackThreshold); }
    public GrowthPolicy setPercentAtCapFallbackThreshold(double v) { this.percentAtCapFallbackThreshold = Math.max(0.0, v); return this; }

    public long getLayerCooldownTicks() { return Math.max(0, layerCooldownTicks); }
    public GrowthPolicy setLayerCooldownTicks(long v) { this.layerCooldownTicks = Math.max(0, v); return this; }

    public boolean isEnableNeuronGrowth() { return enableNeuronGrowth; }
    public GrowthPolicy setEnableNeuronGrowth(boolean v) { this.enableNeuronGrowth = v; return this; }

    public double getNeuronOutlierThresholdPct() { return Math.max(0.0, neuronOutlierThresholdPct); }
    public GrowthPolicy setNeuronOutlierThresholdPct(double v) { this.neuronOutlierThresholdPct = Math.max(0.0, v); return this; }

    public long getNeuronCooldownTicks() { return Math.max(0, neuronCooldownTicks); }
    public GrowthPolicy setNeuronCooldownTicks(long v) { this.neuronCooldownTicks = Math.max(0, v); return this; }

    public long getLastLayerGrowthTick() { return lastLayerGrowthTick; }
    public void setLastLayerGrowthTick(long t) { this.lastLayerGrowthTick = t; }

    public long getLastNeuronGrowthTick() { return lastNeuronGrowthTick; }
    public void setLastNeuronGrowthTick(long t) { this.lastNeuronGrowthTick = t; }
}
