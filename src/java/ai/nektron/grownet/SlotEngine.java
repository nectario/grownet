package ai.nektron.grownet;

public final class SlotEngine {
    private final SlotConfig cfg;

    public SlotEngine(SlotConfig cfg) { this.cfg = cfg; }

    public SlotConfig getConfig() { return cfg; }

    public SlotConfig getConfig() { return cfg; }

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
    /** FIRST-anchor helper with strict capacity + fallback marking.
     *  Chooses desired bin; if out-of-domain or at capacity and new, falls back to a deterministic id.
     *  Never allocates a brand-new slot at capacity (unless this is the very first slot).
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
        int sidDesired = (int) Math.floor(deltaPct / bin);

        int effectiveLimit = (neuron.slotLimit >= 0 ? neuron.slotLimit : cfg.getSlotLimit());
        boolean atCapacity = (effectiveLimit > 0 && neuron.getSlots().size() >= effectiveLimit);
        boolean outOfDomain = (effectiveLimit > 0 && sidDesired >= effectiveLimit);
        boolean wantNew = !neuron.getSlots().containsKey(sidDesired);
        boolean useFallback = outOfDomain || (atCapacity && wantNew);

        int sid = useFallback && effectiveLimit > 0 ? (effectiveLimit - 1) : sidDesired;
        if (!neuron.getSlots().containsKey(sid)) {
            if (atCapacity) {
                if (neuron.getSlots().isEmpty()) {
                    neuron.getSlots().put(sid, new Weight());
                } // else reuse first existing slot implicitly
            } else {
                neuron.getSlots().put(sid, new Weight());
            }
        }
        neuron.lastSlotUsedFallback = useFallback;
        return sid;
    }

    /**
     * Spatial (2D) helper with strict capacity + fallback marking.
     * Uses FIRST spatial anchor; packs (rowBin,colBin) as rowBin*100000 + colBin.
     */
    public int selectOrCreateSlot2D(Neuron neuron, int row, int col, SlotConfig cfg) {
        if (neuron == null) return 0;
        if (cfg == null) cfg = this.cfg;

        // FIRST spatial anchor
        if (neuron.anchorRow < 0 || neuron.anchorCol < 0) {
            neuron.anchorRow = row;
            neuron.anchorCol = col;
        }

        // Simple absolute-bin model aligned with V5 parity (row/col bins by absolute delta)
        int rowBin = Math.abs(row - neuron.anchorRow);
        int colBin = Math.abs(col - neuron.anchorCol);

        int effectiveLimit = (neuron.slotLimit >= 0 ? neuron.slotLimit : cfg.getSlotLimit());
        boolean atCapacity = (effectiveLimit > 0 && neuron.getSlots().size() >= effectiveLimit);
        boolean outOfDomain = (effectiveLimit > 0 && (rowBin >= effectiveLimit || colBin >= effectiveLimit));

        int desiredKey = rowBin * 100000 + colBin;
        boolean wantNew = !neuron.getSlots().containsKey(desiredKey);
        boolean useFallback = outOfDomain || (atCapacity && wantNew);

        int key = useFallback && effectiveLimit > 0
                ? (effectiveLimit - 1) * 100000 + (effectiveLimit - 1)
                : desiredKey;

        if (!neuron.getSlots().containsKey(key)) {
            if (atCapacity) {
                if (neuron.getSlots().isEmpty()) {
                    neuron.getSlots().put(key, new Weight());
                }
            } else {
                neuron.getSlots().put(key, new Weight());
            }
        }
        neuron.lastSlotUsedFallback = useFallback;
        return key;
    }
}
