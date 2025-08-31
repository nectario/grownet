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

    private int fixedBucket(double deltaPercent) {
        if (deltaPercent <= 0.0) return 0;
        return (int)Math.floor((deltaPercent + (cfg.slotWidthPercent - 1.0)) / cfg.slotWidthPercent);
    }

    private int nonuniformBucket(double deltaPercent) {
        int idx = 0;
        for (double edge : cfg.nonuniformEdges) {
            if (deltaPercent <= edge) return idx;
            idx++;
        }
        return idx;
    }

    /**
     * Temporal‑focus helper (FIRST anchor): choose a slot id for input x, ensure a slot exists,
     * and clamp growth at cfg.getSlotLimit() when at capacity.
     */
    public int selectOrCreateSlot(Neuron neuron, double inputValue, SlotConfig cfg) {
        if (neuron == null) return 0;
        if (cfg == null) cfg = this.cfg;

        // Anchor (FIRST)
        if (!neuron.focusSet && cfg.getAnchorMode() == SlotConfig.AnchorMode.FIRST) {
            neuron.focusAnchor = inputValue;
            neuron.focusSet = true;
        }

        double anchor = neuron.focusAnchor;
        double denom = Math.max(Math.abs(anchor), cfg.getEpsilonScale());
        double deltaPct = Math.abs(inputValue - anchor) / denom * 100.0;
        double bin = Math.max(0.1, cfg.getBinWidthPct());
        int slotId = (int) Math.floor(deltaPct / bin);

        // Clamp to slotLimit domain [0, limit-1] if bounded
        int limit = cfg.getSlotLimit();
        if (limit > 0) {
            if (slotId >= limit) slotId = limit - 1;
        }

        // Ensure existence; if at capacity and creating a new id, clamp reuse
        if (!neuron.getSlots().containsKey(slotId)) {
            if (limit > 0 && neuron.getSlots().size() >= limit) {
                // reuse the highest existing id within [0, limit-1]
                slotId = Math.min(slotId, limit - 1);
                if (!neuron.getSlots().containsKey(slotId)) {
                    neuron.getSlots().put(slotId, new Weight());
                }
            } else {
                neuron.getSlots().put(slotId, new Weight());
            }
        }
        return slotId;
    }
}
