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
        Synapse s = new Synapse(target, feedback);
        outgoing.add(s);
        return s;
    }

    // -------- IO --------
    /**
     * Route a scalar in, learn locally, maybe fire. Returns true if fired.
     */
    public boolean onInput(double value) {
        // choose / create slot
        final int slotId = haveLastInput
                ? slotEngine.slotId(lastInputValue, value, slots.size())
                : 0; // imprint
        Weight slot = slots.get(slotId);
        if (slot == null) {
            if (slotLimit >= 0 && slots.size() >= slotLimit) {
                // simple reuse policy: recycle the first slot
                int first = slots.keySet().iterator().next();
                slot = slots.get(first);
            } else {
                slot = new Weight();
                slots.put(slotId, slot);
            }
        }

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
        return fired;
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
        for (BiConsumer<Double, Neuron> h : fireHooks) {
            try { h.accept(amplitude, this); } catch (Exception ignored) { }
        }
    }

    // -------- getters --------
    public Map<Integer, Weight> getSlots()   { return slots; }
    public List<Synapse>        getOutgoing(){ return outgoing; }
    public LateralBus           getBus()     { return bus; }
    public String getId()         { return neuronId; }

    public double getLastInputValue() {
        return lastInputValue;
    }

    public double getFocusAnchor() { return focusAnchor; }
}
