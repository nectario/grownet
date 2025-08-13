package ai.nektron.grownet;

import java.util.*;

/** Base neuron with slot logic. Subclasses can override fire() behaviour. */
public abstract class Neuron {
    /**
     * Optional cap on slot count (null means unlimited).
     */
    public static Integer SLOT_LIMIT = null;

    protected final String neuronId;
    protected LateralBus bus;
    private final List<FireHook> fireHooks = new ArrayList<>();

    protected final Map<Integer, Weight> slots = new LinkedHashMap<>();
    protected final List<Synapse> outgoing = new ArrayList<>();
    protected Double lastInputValue = null;
    protected boolean firedLast = false;

    protected Neuron(String neuronId, LateralBus bus) {
        this.neuronId = neuronId;
        this.bus = bus;
    }

    protected Neuron(String neuronId) {
        this.neuronId = neuronId;
    }

    public String neuronId() {
        return neuronId;
    }

    public Map<Integer, Weight> slots() {
        return slots;
    }

    public List<Synapse> outgoing() {
        return outgoing;
    }


    public java.util.List<Synapse> getOutgoing() {
        return outgoing;
    }

    public Double getLastInputValue() { return lastInputValue; }

    // 1) Add (or keep) these accessors
    public java.util.Map<Integer, Weight> getSlots() { return slots; }


    // 2) Replace the body of your protected selectSlot(double inputValue) with:
    protected Weight selectSlot(double inputValue) {
        int bucket = SlotPolicyEngine.selectOrCreateSlot(this, inputValue, SlotPolicyConfig.defaults());
        // selectOrCreateSlot has ensured presence in 'slots'
        return slots.get(bucket);
    }

    /**
     * Route input into a slot, learn locally, maybe fire.
     */
    public void onInput(double inputValue) {
        Weight slot = selectSlot(inputValue);
        slot.reinforce(bus.modulationFactor(), bus.inhibitionFactor());
        if (slot.updateThreshold(inputValue)) fire(inputValue);
        lastInputValue = inputValue;
    }

    /**
     * Create a new synapse to target and return it (fluent style).
     */
    public Synapse connect(Neuron target, boolean feedback) {
        Synapse s = new Synapse(target, feedback);
        outgoing.add(s);
        return s;
    }

    /**
     * Drop stale + weak synapses.
     */
    public void pruneSynapses(long currentStep, long staleWindow, double minStrength) {
        outgoing.removeIf(s -> {
            boolean stale = (currentStep - s.lastStep) > staleWindow;
            boolean weak = s.getWeight().getStrengthValue() < minStrength;
            return stale && weak;
        });
    }

    /**
     * Default excitatory behaviour: propagate along outgoing synapses.
     */
    public void fire(double inputValue) {
        for (Synapse s : outgoing) {
            s.weight.reinforce(bus.modulationFactor(), bus.inhibitionFactor());
            s.lastStep = bus.currentStep();
            if (s.weight.updateThreshold(inputValue)) {
                s.target.onInput(inputValue);
            }
        }

        for (FireHook hook : fireHooks) {
            hook.onFire(inputValue, this);
        }
    }



    // inside class Neuron
    public double neuronValue(String mode) {
        if (slots.isEmpty()) return 0.0;
        String m = mode.toLowerCase();
        switch (m) {
            case "readiness": {
                double best = Double.NEGATIVE_INFINITY;
                for (Weight w : slots.values()) {
                    double margin = w.getStrengthValue() - w.getThresholdValue();
                    if (margin > best) best = margin;
                }
                return best;
            }
            case "firing_rate": {
                double sum = 0.0;
                for (Weight w : slots.values())
                    sum +=
                            (w.getStrengthValue() > w.getThresholdValue() ? 1.0 : 0.0);
                return sum / slots.size();
            }
            case "memory": {
                double sum = 0.0;
                for (Weight w : slots.values()) sum += Math.abs(w.getStrengthValue());
                return sum;
            }
            default:
                throw new IllegalArgumentException("Unknown mode: " + mode);
        }
    }

    public void registerFireHook(FireHook hook) {
        fireHooks.add(hook);
    }

    public void onOutput(double amplitude) { /* no-op by default */ }

    public void setLastInputValue(Double lastInputValue) {
        this.lastInputValue = lastInputValue;
    }

    public boolean isFiredLast() {
        return firedLast;
    }

    public void setFiredLast(boolean firedLast) {
        this.firedLast = firedLast;
    }

}
