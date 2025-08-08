package ai.nektron.grownet;

import java.util.*;

/** Base neuron with slot logic. Subclasses can override fire() behaviour. */
public abstract class Neuron {
    /** Optional cap on slot count (null means unlimited). */
    public static Integer SLOT_LIMIT = null;

    protected final String neuronId;
    protected final LateralBus bus;
    private final List<FireHook> fireHooks = new ArrayList<>();

    protected final Map<Integer, Weight> slots = new LinkedHashMap<>();
    protected final List<Synapse> outgoing = new ArrayList<>();
    protected Double lastInputValue = null;


    protected Neuron(String neuronId, LateralBus bus) {
        this.neuronId = neuronId;
        this.bus = bus;
    }

    public String neuronId() { return neuronId; }
    public Map<Integer, Weight> slots() { return slots; }
    public List<Synapse> outgoing() { return outgoing; }

    public java.util.Map<Integer, Weight> getSlots() { return slots; }
    public java.util.List<Synapse> getOutgoing()     { return outgoing; }

    /** Route input into a slot, learn locally, maybe fire. */
    public void onInput(double inputValue) {
        Weight slot = selectSlot(inputValue);
        slot.reinforce(bus.modulationFactor(), bus.inhibitionFactor());
        if (slot.updateThreshold(inputValue)) fire(inputValue);
        lastInputValue = inputValue;
    }

    /** Create a new synapse to target and return it (fluent style). */
    public Synapse connect(Neuron target, boolean feedback) {
        Synapse s = new Synapse(target, feedback);
        outgoing.add(s);
        return s;
    }

    /** Drop stale + weak synapses. */
    public void pruneSynapses(long currentStep, long staleWindow, double minStrength) {
        outgoing.removeIf(s ->
                (currentStep - s.lastStep) > staleWindow && s.weight.getStrengthValue() < minStrength
        );
    }


    /** Default excitatory behaviour: propagate along outgoing synapses. */
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

    /** Route to a slot based on percent delta from last input. */
    protected Weight selectSlot(double inputValue) {
        int binId;
        if (lastInputValue == null || lastInputValue == 0.0) {
            binId = 0;
        } else {
            double delta = Math.abs(inputValue - lastInputValue) / Math.abs(lastInputValue);
            double deltaPercent = delta * 100.0;
            binId = (deltaPercent == 0.0) ? 0 : (int) Math.ceil(deltaPercent / 10.0);
        }

        Weight slot = slots.get(binId);
        if (slot == null) {
            if (SLOT_LIMIT != null && slots.size() >= SLOT_LIMIT) {
                // trivial reuse policy: earliest created slot
                slot = slots.values().iterator().next();
            } else {
                slot = new Weight();
                slots.put(binId, slot);
            }
        }
        return slot;
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
                for (Weight w : slots.values()) sum += /* emaRate not exposed; add a getter if you want exact parity */
                        // quick proxy if you don't want to expose emaRate:
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

}
