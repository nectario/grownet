package ai.nektron.grownet;

import java.util.*;
import java.util.function.BiConsumer;

/** Base neuron containing slot logic and fan-out synapses (intra-layer). */
public abstract class Neuron {
    public static int slotLimit = -1; // negative = unlimited

    protected final String neuronId;
    protected final LateralBus bus;

    protected final Map<Integer, Weight> slots = new HashMap<>();
    protected final List<Synapse> outgoing = new ArrayList<>();

    protected boolean hasLastInput = false;
    protected double lastInputValue = 0.0;

    protected SlotPolicy slotPolicy = SlotPolicy.uniformFixed(10.0);

    private final List<FireHook> fireHooks = new ArrayList<>();

    protected Neuron(String neuronId, LateralBus bus) {
        this.neuronId = neuronId;
        this.bus = bus;
    }

    public String getId() { return neuronId; }
    public Map<Integer, Weight> getSlots() { return slots; }
    public List<Synapse> getOutgoing() { return outgoing; }
    public LateralBus getBus() { return bus; }

    public void setSlotPolicy(SlotPolicy policy) { this.slotPolicy = policy; }

    /** External input arrives here (or routed input from tracts). */
    public void onInput(double inputValue) {
        Weight slot = selectSlot(inputValue);
        slot.reinforce(bus.getModulationScale(), bus.getInhibitionFactor());
        if (slot.updateThreshold(inputValue)) {
            fire(inputValue);
        }
        hasLastInput = true;
        lastInputValue = inputValue;
    }

    /** Called when this neuron should emit to the outside world (for OutputNeuron). */
    public void onOutput(double amplitude) {
        // default no-op; OutputNeuron overrides
    }

    /** Default excitatory fire: fan-out to outgoing synapses. Subclasses override as needed. */
    protected void fire(double inputValue) {
        for (Synapse syn : outgoing) {
            syn.getWeight().reinforce(bus.getModulationScale(), bus.getInhibitionFactor());
            syn.lastStep = bus.getCurrentStep();
            if (syn.getWeight().updateThreshold(inputValue) && syn.getTarget() != null) {
                syn.getTarget().onInput(inputValue);
            }
        }
        for (FireHook hook : fireHooks) {
            hook.onFire(inputValue, this);
        }
    }

    /** Connect to another neuron within the same layer. */
    public Synapse connect(Neuron target, boolean isFeedback) {
        Synapse s = new Synapse(target, isFeedback);
        outgoing.add(s);
        return s;
    }

    /** Remove stale + weak synapses. */
    public void pruneSynapses(long currentStep, long staleWindow, double minStrength) {
        outgoing.removeIf(s -> (currentStep - s.lastStep) > staleWindow
                && s.getWeight().getStrength() < minStrength);
    }

    /** Scalar summaries for logging. */
    public double neuronValue(String mode) {
        if (slots.isEmpty()) return 0.0;
        switch (mode) {
            case "firing_rate": {
                double sum = 0.0;
                for (Weight w : slots.values()) sum += w.getEmaRate();
                return sum / slots.size();
            }
            case "memory": {
                double sum = 0.0;
                for (Weight w : slots.values()) sum += Math.abs(w.getStrength());
                return sum;
            }
            case "readiness":
            default: {
                double best = -1e300;
                for (Weight w : slots.values()) {
                    double margin = w.getStrength() - w.getThreshold();
                    if (margin > best) best = margin;
                }
                return best;
            }
        }
    }

    /** Choose a slot by percent-delta policy, respecting slotLimit. */
    protected Weight selectSlot(double inputValue) {
        int binId = slotPolicy.slotId(lastInputValue, hasLastInput, inputValue);
        Weight w = slots.get(binId);
        if (w == null) {
            if (slotLimit >= 0 && slots.size() >= slotLimit) {
                // simple reuse policy: return the lowest-key slot
                int firstKey = Collections.min(slots.keySet());
                return slots.get(firstKey);
            }
            w = new Weight();
            slots.put(binId, w);
        }
        return w;
    }

    public void registerFireHook(FireHook hook) { fireHooks.add(hook); }
}