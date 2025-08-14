package ai.nektron.grownet;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

/**
 * Base neuron with slot logic and unified onInput/onOutput hooks.
 * Subclasses override fire() for excitatory/inhibitory/modulatory behavior.
 */
public class Neuron {

    // ----------------------------- state -----------------------------

    protected final String neuronId;
    protected final LateralBus bus;

    // slotId -> Weight
    protected final Map<Integer, Weight> slots = new HashMap<>();

    // outgoing synapses (fan‑out is owned here; fan‑in owned by target)
    protected final List<Synapse> outgoing = new ArrayList<>();

    // slot selection policy
    protected final SlotEngine slotEngine;
    protected final int slotLimit;   // -1 => unlimited

    // last‑input bookkeeping (for %‑delta based slotting)
    protected boolean haveLastInput = false;
    protected double  lastInputValue = 0.0;

    // --------------------------- lifecycle ---------------------------

    public Neuron(String neuronId,
                  LateralBus bus,
                  SlotConfig slotConfig,
                  int slotLimit) {
        this.neuronId   = neuronId;
        this.bus        = bus;
        this.slotEngine = new SlotEngine(slotConfig);
        this.slotLimit  = slotLimit;
    }

    // ----------------------------- wiring ----------------------------

    /** Create an outgoing synapse to a target neuron. */
    public Synapse connect(Neuron target, boolean feedback) {
        Synapse s = new Synapse(target, feedback);
        outgoing.add(s);
        return s;
    }

    // ------------------------------ I/O ------------------------------

    /**
     * Route to a slot, learn locally, maybe fire. Returns true if fired.
     */
    public boolean onInput(double value) {
        // pick/create a slot keyed by percent‑delta of current vs last input
        int slotId = haveLastInput
                ? slotEngine.slotId(lastInputValue, value, slots.size())
                : 0;  // imprint into slot 0 if this is the first input

        Weight slot = slots.get(slotId);
        if (slot == null) {
            // capacity cap (very simple policy: reuse the first slot)
            if (slotLimit >= 0 && slots.size() >= slotLimit) {
                int first = slots.keySet().iterator().next();
                slot = slots.get(first);
            } else {
                slot = new Weight();
                slots.put(slotId, slot);
            }
        }

        // local learning on the chosen slot; scale by neuromodulation
        slot.reinforce(bus.getModulationFactor());

        // adaptive threshold update; decide whether we fired
        boolean fired = slot.updateThreshold(value);
        if (fired) fire(value);

        haveLastInput = true;
        lastInputValue = value;
        return fired;
    }

    public double getLastInputValue() {
        return lastInputValue;
    }



    /**
     * Default no‑op; OutputNeuron overrides to expose values to the outside world.
     */
    public void onOutput(double amplitude) {
        // no‑op by default
    }

    // ------------------------- spike semantics -----------------------

    /**
     * Default spike behavior is handled in subclasses (Excitatory, Inhibitory, Modulatory).
     * Base class only keeps the unified API coherent.
     */
    protected void fire(double inputValue) {
        // override in subclasses
    }

    // ---------------------------- logging ----------------------------

    /**
     * Small scalar summaries, useful for dashboards.
     * mode ∈ { "readiness", "firing_rate", "memory" }
     */
    public double neuronValue(String mode) {
        if (slots.isEmpty()) return 0.0;

        switch (mode) {
            case "readiness": {
                double best = -1e300;
                for (Weight w : slots.values()) {
                    double margin = w.strengthValue - w.thresholdValue;
                    if (margin > best) best = margin;
                }
                return best;
            }
            case "firing_rate": {
                double sum = 0.0;
                for (Weight w : slots.values()) sum += w.emaRate;
                return sum / slots.size();
            }
            case "memory": {
                double acc = 0.0;
                for (Weight w : slots.values()) acc += Math.abs(w.strengthValue);
                return acc;
            }
            default:
                return neuronValue("readiness");
        }
    }

    // --------------------------- accessors ---------------------------

    /** Preferred accessor used by new code. */
    public Map<Integer, Weight> slots() { return slots; }

    /** Preferred accessor used by new code. */
    public List<Synapse> outgoing() { return outgoing; }

    public LateralBus bus() { return bus; }

    public String id() { return neuronId; }

    // --------- compatibility shims for Region/Demo/older callers -----

    /** Alias for Region/Demo code that expects getSlots(). */
    public Map<Integer, Weight> getSlots() { return slots(); }

    /** Alias for Region/Demo code that expects getOutgoing(). */
    public List<Synapse> getOutgoing() { return outgoing(); }

    // --------------------------- maintenance -------------------------

    /**
     * Remove weak (and, in the future, stale) outgoing synapses.
     * @param synapseStaleWindow   reserved; staleness will be used when Synapse exposes lastStep
     * @param synapseMinStrength   edges with weight.strengthValue below this are pruned
     * @return number of synapses removed
     */
    public int pruneSynapses(long synapseStaleWindow, double synapseMinStrength) {
        int removed = 0;
        List<Synapse> keep = new ArrayList<>(outgoing.size());
        for (Synapse s : outgoing) {
            boolean weak = (s.getWeight() != null) && (s.getWeight().strengthValue < synapseMinStrength);

            // TODO: when Synapse exposes lastStep and LateralBus exposes currentStep,
            //       also consider staleness: now - s.lastStep > synapseStaleWindow.
            boolean stale = false;

            if (weak && stale) {
                removed++;
            } else if (weak) {
                // If you prefer to prune on weakness alone (current default), keep stale==false
                removed++;
            } else {
                keep.add(s);
            }
        }
        outgoing.clear();
        outgoing.addAll(keep);
        return removed;
    }
}
