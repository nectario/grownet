package ai.nektron.grownet;

import java.util.*;

public class Neuron {
    protected final String neuronId;
    protected final LateralBus bus;
    protected final Map<Integer, Weight> slots = new HashMap<>();
    protected final List<Synapse> outgoing = new ArrayList<>();
    protected final SlotEngine slotEngine;
    protected final int slotLimit; // -1 = unbounded

    protected boolean haveLastInput = false;
    protected double  lastInputValue = 0.0;

    public Neuron(String neuronId, LateralBus bus,
                  SlotConfig slotConfig, int slotLimit) {
        this.neuronId = neuronId;
        this.bus = bus;
        this.slotEngine = new SlotEngine(slotConfig);
        this.slotLimit = slotLimit;
    }

    // ---- wiring -----------------------------------------------------------
    public Synapse connect(Neuron target, boolean feedback) {
        Synapse s = new Synapse(target, feedback);
        outgoing.add(s);
        return s;
    }

    // ---- IO ---------------------------------------------------------------
    public boolean onInput(double value) {
        int slotId = haveLastInput
                ? slotEngine.slotId(lastInputValue, value, slots.size())
                : 0; // T0 imprint

        Weight slot = slots.get(slotId);
        if (slot == null) {
            if (slotLimit >= 0 && slots.size() >= slotLimit) {
                // trivial reuse: first slot
                int first = slots.keySet().iterator().next();
                slot = slots.get(first);
            } else {
                slot = new Weight();
                slots.put(slotId, slot);
            }
        }

        slot.reinforce(bus.modulationFactor());
        boolean fired = slot.updateThreshold(value);
        if (fired) fire(value);

        haveLastInput = true;
        lastInputValue = value;
        return fired;
    }

    public void onOutput(double amplitude) {
        // default no-op; OutputNeuron overrides
    }

    // ---- spike semantics --------------------------------------------------
    protected void fire(double inputValue) {
        // default excitatory semantics handled in subclass;
        // base keeps the unified API coherent.
    }

    // ---- small introspection ---------------------------------------------
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
            default: return neuronValue("readiness");
        }
    }

    // accessors
    public Map<Integer, Weight> slots() { return slots; }
    public List<Synapse> outgoing() { return outgoing; }
    public LateralBus bus() { return bus; }
    public String id() { return neuronId; }
}
