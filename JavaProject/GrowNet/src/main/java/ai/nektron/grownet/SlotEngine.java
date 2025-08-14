package ai.nektron.grownet;

public final class SlotEngine {
    private final SlotConfig cfg;

    public SlotEngine(SlotConfig cfg) { this.cfg = cfg; }

    public int slotId(double lastInput, double newInput, int slotsLen) {
        double deltaPercent = 0.0;
        if (lastInput != 0.0) {
            deltaPercent = Math.abs(newInput - lastInput) / Math.abs(lastInput) * 100.0;
        }
        switch (cfg.policy) {
            case FIXED:      return fixedBucket(deltaPercent);
            case NONUNIFORM: return nonuniformBucket(deltaPercent);
            case ADAPTIVE:   return fixedBucket(deltaPercent); // base id; overflow handled by caller
        }
        return 0;
    }

    private int fixedBucket(double dp) {
        if (dp <= 0.0) return 0;
        return (int)Math.floor((dp + (cfg.slotWidthPercent - 1.0)) / cfg.slotWidthPercent);
    }

    private int nonuniformBucket(double dp) {
        int idx = 0;
        for (double edge : cfg.nonuniformEdges) {
            if (dp <= edge) return idx;
            idx++;
        }
        return idx;
    }
}
