package ai.nektron.grownet;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.function.BiConsumer;

import static java.lang.Math.abs;

/**
 * Base neuron with slot logic and unified onInput/onOutput contract.
 * Subclasses override fire(...) for excitatory / inhibitory / modulatory behaviour.
 */
public class Neuron {

    // -------- state --------
    protected final String neuronId;
    protected final LateralBus bus;

    // slot memory: key = slot id, val = weight
    protected final Map<Integer, Weight> slots = new HashMap<>();
    protected Integer lastSlotId = null; // remember most recent slot id

    // explicit synapses (kept for future, even if Tract handles layer–layer routing)
    protected final List<Synapse> outgoing = new ArrayList<>();

    // slot policy + optional cap
    protected final SlotEngine slotEngine;
    protected final int       slotLimit;   // -1 = unbounded

    // last input (for %delta binning)
    protected boolean haveLastInput = false;
    protected double  lastInputValue = 0.0;

    // Temporal focus (anchor-based)
    protected double  focusAnchor = 0.0;
    protected boolean focusSet = false;
    protected long    focusLockUntilTick = 0L;

    // Growth + parity fields
    public boolean lastSlotUsedFallback = false;
    public int     fallbackStreak = 0;
    public long    lastGrowthTick = -1L;
    public int     prevMissingSlotId = -1;
    public int     lastMissingSlotId = -1;
    public double  lastMaxAxisDeltaPct = 0.0;
    public boolean preferLastSlotOnce = false; // one-shot reuse (legacy)
    // Track the specific slot frozen and a one-shot preference for that slot on unfreeze
    private Integer frozenSlotId = null;
    private Integer preferSlotIdOnce = null;
    public Layer   owner = null;               // backref set by Layer
    // Spatial (2D) FIRST anchor
    public int anchorRow = -1;
    public int anchorCol = -1;

    // NEW: hooks notified whenever this neuron fires
    private final List<BiConsumer<Double, Neuron>> fireHooks = new ArrayList<>();

    // -------- construction --------
    public Neuron(String neuronId, LateralBus bus, SlotConfig slotConfig, int slotLimit) {
        this.neuronId   = neuronId;
        this.bus        = bus;
        this.slotEngine = new SlotEngine(slotConfig);
        this.slotLimit  = slotLimit;
    }

    // -------- wiring (optional, still useful for unit tests) --------
    public Synapse connect(Neuron target, boolean feedback) {
        Synapse edge = new Synapse(target, feedback);
        outgoing.add(edge);
        return edge;
    }

    // -------- IO --------
    /**
     * Route a scalar in, learn locally, maybe fire. Returns true if fired.
     */
    public boolean onInput(double value) {
        // V4 Temporal Focus (FIRST anchor): choose/create slot with strict capacity
        final int slotId;
        if (preferSlotIdOnce != null) {
            slotId = preferSlotIdOnce;
        } else if (preferLastSlotOnce && lastSlotId != null) {
            slotId = lastSlotId;
        } else {
            slotId = slotEngine.selectOrCreateSlot(this, value, /*cfg*/ null);
        }
        // Clear one-shot hints after use
        preferSlotIdOnce = null;
        preferLastSlotOnce = false;
        lastSlotId = slotId;
        Weight slot = slots.get(slotId); // existence ensured by SlotEngine

        // learn under neuromodulation
        slot.reinforce(bus.getModulationFactor());

        // update the adaptive threshold and decide
        boolean fired = slot.updateThreshold(value);
        if (fired) {
            fire(value);                // subtype behaviour
            notifyFireHooks(value);     // <— Tract listens here
        }

        haveLastInput  = true;
        lastInputValue = value;
        // Growth bookkeeping (best effort): at-capacity + fallback streak
        try {
            final SlotConfig C = slotEngine == null ? null : slotEngine.getConfig();
            if (C != null && C.isGrowthEnabled() && C.isNeuronGrowthEnabled()) {
                final boolean atCap = (slotLimit >= 0 && slots.size() >= slotLimit);
                if (!(atCap && lastSlotUsedFallback)) {
                    fallbackStreak = 0;
                    prevMissingSlotId = -1;
                    lastMissingSlotId = -1;
                    return fired;
                }
                if (C.getMinDeltaPctForGrowth() > 0.0) {
                    if (lastMaxAxisDeltaPct < C.getMinDeltaPctForGrowth()) {
                        fallbackStreak = 0;
                        prevMissingSlotId = -1;
                        return fired;
                    }
                }
                if (C.isFallbackGrowthRequiresSameMissingSlot()) {
                    if (prevMissingSlotId == lastMissingSlotId) {
                        fallbackStreak++;
                    } else {
                        fallbackStreak = 1;
                        prevMissingSlotId = lastMissingSlotId;
                    }
                } else {
                    fallbackStreak++;
                }
                final int threshold = Math.max(1, C.getFallbackGrowthThreshold());
                if (fallbackStreak >= threshold) {
                    final long now = bus.getCurrentStep();
                    final int cooldown = Math.max(0, C.getNeuronGrowthCooldownTicks());
                    if (owner != null && (lastGrowthTick < 0 || (now - lastGrowthTick) >= cooldown)) {
                        try { owner.tryGrowNeuron(this); } catch (Throwable ignored) { }
                        lastGrowthTick = now;
                    }
                    // Reset streak and ids whether or not growth occurred, matching Python semantics
                    fallbackStreak = 0;
                    prevMissingSlotId = -1;
                    lastMissingSlotId = -1;
                }
            }
        } catch (Throwable ignored) { }
        return fired;
    }

    /**
     * 2D on-input path (strict capacity + fallback marking + growth bookkeeping).
     * Mirrors the scalar path, but uses the 2D selector and spatial anchors.
     */
    public boolean onInput2D(double value, int row, int col) {
        final int slotId;
        if (preferSlotIdOnce != null) {
            slotId = preferSlotIdOnce;
        } else if (preferLastSlotOnce && lastSlotId != null) {
            slotId = lastSlotId;
        } else {
            slotId = slotEngine.selectOrCreateSlot2D(this, row, col, /*cfg*/ null);
        }
        preferSlotIdOnce = null;
        preferLastSlotOnce = false;
        lastSlotId = slotId;

        Weight slot = slots.get(slotId);
        slot.reinforce(bus.getModulationFactor());
        boolean fired = slot.updateThreshold(value);
        if (fired) {
            fire(value);
            notifyFireHooks(value);
            onOutput(value);
        }
        haveLastInput  = true;
        lastInputValue = value;

        // Growth bookkeeping parity with scalar onInput
        try {
            final SlotConfig C = slotEngine == null ? null : slotEngine.getConfig();
            if (C != null && C.isGrowthEnabled() && C.isNeuronGrowthEnabled()) {
                final boolean atCap = (slotLimit >= 0 && slots.size() >= slotLimit);
                if (!(atCap && lastSlotUsedFallback)) {
                    fallbackStreak = 0;
                    prevMissingSlotId = -1;
                    lastMissingSlotId = -1;
                    return fired;
                }
                if (C.getMinDeltaPctForGrowth() > 0.0) {
                    if (lastMaxAxisDeltaPct < C.getMinDeltaPctForGrowth()) {
                        fallbackStreak = 0;
                        prevMissingSlotId = -1;
                        return fired;
                    }
                }
                if (C.isFallbackGrowthRequiresSameMissingSlot()) {
                    if (prevMissingSlotId == lastMissingSlotId) {
                        fallbackStreak++;
                    } else {
                        fallbackStreak = 1;
                        prevMissingSlotId = lastMissingSlotId;
                    }
                } else {
                    fallbackStreak++;
                }
                final int threshold = Math.max(1, C.getFallbackGrowthThreshold());
                if (fallbackStreak >= threshold) {
                    final long now = bus.getCurrentStep();
                    final int cooldown = Math.max(0, C.getNeuronGrowthCooldownTicks());
                    if (owner != null && (lastGrowthTick < 0 || (now - lastGrowthTick) >= cooldown)) {
                        try { owner.tryGrowNeuron(this); } catch (Throwable ignored) { }
                        lastGrowthTick = now;
                    }
                    fallbackStreak = 0;
                    prevMissingSlotId = -1;
                    lastMissingSlotId = -1;
                }
            }
        } catch (Throwable ignored) { }
        return fired;
    }

    // -------- Frozen-slot convenience --------
    public boolean freezeLastSlot() {
        if (lastSlotId == null) return false;
        Weight w = slots.get(lastSlotId);
        if (w == null) return false;
        w.freeze();
        frozenSlotId = lastSlotId;
        return true;
    }

    public boolean unfreezeLastSlot() {
        Integer targetId = (frozenSlotId != null) ? frozenSlotId : lastSlotId;
        if (targetId == null) return false;
        Weight w = slots.get(targetId);
        if (w == null) return false;
        w.unfreeze();
        // Prefer the originally frozen slot once on the next selection
        preferSlotIdOnce = targetId;
        frozenSlotId = null;
        return true;
    }

    /**
     * Default no‑op; OutputNeuron overrides to expose values externally.
     */
    public void onOutput(double amplitude) { /* no‑op by default */ }

    /**
     * Subclasses override to implement excitatory / inhibitory / modulatory semantics.
     * Base keeps the unified signature but does not enforce behaviour.
     */
    protected void fire(double inputValue) { /* handled by subclasses */ }

    // -------- small introspection used by demos --------
    public double neuronValue(String mode) {
        if (slots.isEmpty()) return 0.0;

        switch (mode) {
            case "readiness": {
                double best = -1e300;
                for (Weight weight : slots.values()) {
                    double margin = weight.getStrengthValue() - weight.getThresholdValue();
                    if (margin > best) best = margin;
                }
                return best;
            }
            case "firing_rate": {
                double sum = 0.0;
                for (Weight weight : slots.values()) {
                    sum += weight.getEmaRate();
                }
                return sum / slots.size();
            }
            case "memory": {
                double acc = 0.0;
                for (Weight weight : slots.values()) {
                    acc += Math.abs(weight.getStrengthValue());
                }
                return acc;
            }
            default:
                return neuronValue("readiness");
        }
    }

    // Neuron.java  — add inside class Neuron
    /**
     * Remove outgoing synapses that are both stale and weak.
     *
     * @param staleWindow        prune if (currentStep - lastStep) > staleWindow
     * @param minStrength        prune if weight.strength < minStrength
     * @return number of synapses removed
     */
    public int pruneSynapses(long staleWindow, double minStrength) {
        int removed = 0;
        final long currentStep = bus.getCurrentStep();   // LateralBus (layer bus) step

        // Keep list to avoid ConcurrentModificationException
        final List<Synapse> keep = new ArrayList<>(outgoing.size());
        for (Synapse synapse : outgoing) {
            final long    lastStep      = synapse.getLastStep();
            final double  strength      = synapse.getWeight().getStrengthValue();
            final boolean isStale       = (currentStep - lastStep) > staleWindow;
            final boolean isWeak        = strength < minStrength;

            if (isStale && isWeak) {
                removed += 1;
                // drop this synapse
            } else {
                keep.add(synapse);
            }
        }
        outgoing.clear();
        outgoing.addAll(keep);
        return removed;
    }

    
    // -------- hooks API (used by Tract) --------

    /** Register a hook (value, who) called every time this neuron fires. */
    public void registerFireHook(BiConsumer<Double, Neuron> hook) {
        if (hook != null) fireHooks.add(hook);
    }

    /** Bridge if you kept a custom functional interface FireHook. */
    public void registerFireHook(FireHook hook) {
        if (hook != null) fireHooks.add((v, who) -> hook.onFire(v, who));
    }

    private void notifyFireHooks(double amplitude) {
        for (BiConsumer<Double, Neuron> hook : fireHooks) {
            try { hook.accept(amplitude, this); } catch (Exception ignored) { }
        }
    }

    // -------- getters --------
    public Map<Integer, Weight> getSlots()   { return slots; }
    public List<Synapse>        getOutgoing(){ return outgoing; }
    public LateralBus           getBus()     { return bus; }
    public String getId()         { return neuronId; }
    public int getSlotLimit()     { return slotLimit; }

    public double getLastInputValue() {
        return lastInputValue;
    }

    public double getFocusAnchor() { return focusAnchor; }
}
