package ai.nektron.grownet;

public class InputNeuron extends Neuron {
    public InputNeuron(String id, LateralBus bus, SlotConfig cfg) {
        super(id, bus, cfg, 1); // single-slot
    }
    @Override public boolean onInput(double value) {
        Weight slot = slots.getOrDefault(0, new Weight());
        slots.putIfAbsent(0, slot);

        slot.reinforce(bus.modulationFactor());
        boolean fired = slot.updateThreshold(value);
        if (fired) fire(value);

        haveLastInput  = true;
        lastInputValue = value;
        return fired;
    }
}
