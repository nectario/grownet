package ai.nektron.grownet;

import java.util.ArrayList;
import java.util.List;

public final class SlotConfig {
    public enum Policy { FIXED, NONUNIFORM, ADAPTIVE }
    public enum AnchorMode { FIRST, EMA, WINDOW, LAST }

    public Policy policy = Policy.FIXED;
    public double slotWidthPercent = 10.0;      // FIXED/ADAPTIVE seed
    public final List<Double> nonuniformEdges = new ArrayList<>(); // ascending
    public int maxSlots = -1;                   // -1 = unbounded

    // ---------------- Temporal‑focus knobs (conservative defaults) ----------------
    private AnchorMode anchorMode = AnchorMode.FIRST;   // initial anchor strategy
    private double binWidthPct = 10.0;                  // %Δ per slot bin
    private double epsilonScale = 1e-6;                 // guard for near‑zero anchors
    private double recenterThresholdPct = 35.0;         // when to consider re‑anchoring
    private int    recenterLockTicks = 20;              // cooldown on re‑anchoring
    private double anchorBeta = 0.05;                   // EMA for EMA/WINDOW modes
    private double outlierGrowthThresholdPct = 60.0;    // signals potential neuron growth
    private int    slotLimit = 16;                      // cap slots per neuron (soft)

    // ---------------- Growth knobs (parity with Python; conservative defaults) ----------------
    private boolean growthEnabled = true;
    private boolean neuronGrowthEnabled = true;
    private int     neuronGrowthCooldownTicks = 0;
    private int     fallbackGrowthThreshold = 3;

    public SlotConfig() {}
    public static SlotConfig fixed(double widthPercent) {
        SlotConfig c = new SlotConfig();
        c.policy = Policy.FIXED;
        c.slotWidthPercent = widthPercent;
        return c;
    }
    public static SlotConfig nonuniform(List<Double> edgesAsc) {
        SlotConfig c = new SlotConfig();
        c.policy = Policy.NONUNIFORM;
        c.nonuniformEdges.addAll(edgesAsc);
        return c;
    }
    public static SlotConfig adaptive(double seedWidthPercent, int maxSlots) {
        SlotConfig c = new SlotConfig();
        c.policy = Policy.ADAPTIVE;
        c.slotWidthPercent = seedWidthPercent;
        c.maxSlots = maxSlots;
        return c;
    }



    // SlotConfig.java  — add inside the class
    /** Convenience: one-slot behaviour used by InputNeuron. */
    public static SlotConfig singleSlot() {
        // 100% bucket width means every delta falls into the same bucket;
        // InputNeuron also passes slotLimit = 1 to the Neuron base.
        return fixed(100.0);   // or `fixed(100.0)` if your factory is named `fixed`
    }

    // ---------------- getters/setters for temporal‑focus knobs ----------------
    public AnchorMode getAnchorMode() { return anchorMode; }
    public SlotConfig setAnchorMode(AnchorMode mode) { this.anchorMode = (mode == null ? AnchorMode.FIRST : mode); return this; }

    public double getBinWidthPct() { return clampPct(binWidthPct, 0.1, 1000.0); }
    public SlotConfig setBinWidthPct(double value) { this.binWidthPct = clampPct(value, 0.1, 1000.0); return this; }

    public double getEpsilonScale() { return Math.max(1e-12, epsilonScale); }
    public SlotConfig setEpsilonScale(double value) { this.epsilonScale = Math.max(1e-12, value); return this; }

    public double getRecenterThresholdPct() { return clampPct(recenterThresholdPct, 0.0, 10_000.0); }
    public SlotConfig setRecenterThresholdPct(double value) { this.recenterThresholdPct = clampPct(value, 0.0, 10_000.0); return this; }

    public int getRecenterLockTicks() { return Math.max(0, recenterLockTicks); }
    public SlotConfig setRecenterLockTicks(int ticks) { this.recenterLockTicks = Math.max(0, ticks); return this; }

    public double getAnchorBeta() { return clampPct(anchorBeta, 0.0, 1.0); }
    public SlotConfig setAnchorBeta(double value) { this.anchorBeta = clampPct(value, 0.0, 1.0); return this; }

    public double getOutlierGrowthThresholdPct() { return clampPct(outlierGrowthThresholdPct, 0.0, 1_000_000.0); }
    public SlotConfig setOutlierGrowthThresholdPct(double value) { this.outlierGrowthThresholdPct = clampPct(value, 0.0, 1_000_000.0); return this; }

    public int getSlotLimit() { return slotLimit; }
    public SlotConfig setSlotLimit(int limit) { this.slotLimit = (limit < 0 ? -1 : limit); return this; }

    public boolean isGrowthEnabled() { return growthEnabled; }
    public SlotConfig setGrowthEnabled(boolean v) { this.growthEnabled = v; return this; }
    public boolean isNeuronGrowthEnabled() { return neuronGrowthEnabled; }
    public SlotConfig setNeuronGrowthEnabled(boolean v) { this.neuronGrowthEnabled = v; return this; }
    public int getNeuronGrowthCooldownTicks() { return Math.max(0, neuronGrowthCooldownTicks); }
    public SlotConfig setNeuronGrowthCooldownTicks(int t) { this.neuronGrowthCooldownTicks = Math.max(0, t); return this; }
    public int getFallbackGrowthThreshold() { return Math.max(1, fallbackGrowthThreshold); }
    public SlotConfig setFallbackGrowthThreshold(int t) { this.fallbackGrowthThreshold = Math.max(1, t); return this; }

    private static double clampPct(double value, double lowerBound, double upperBound) {
        if (Double.isNaN(value) || Double.isInfinite(value)) return lowerBound;
        return Math.max(lowerBound, Math.min(upperBound, value));
    }

}
