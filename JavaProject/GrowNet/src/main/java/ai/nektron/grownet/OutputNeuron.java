package ai.nektron.grownet;

public class OutputNeuron extends Neuron {
    private double lastEmitted = 0.0;

    public OutputNeuron(String id, LateralBus bus, SlotConfig cfg) {
        super(id, bus, cfg, 1); // single-slot sink
    }

    @Override public boolean onInput(double value) {
        Weight slot = slots.getOrDefault(0, new Weight());
        slots.putIfAbsent(0, slot);

        slot.reinforce(bus.getModulationFactor());
        boolean fired = slot.updateThreshold(value);
        if (fired) onOutput(value);

        haveLastInput  = true;
        lastInputValue = value;
        return fired;
    }

    @Override public void onOutput(double amplitude) {
        lastEmitted = amplitude;
    }

    public double lastEmitted() { return lastEmitted; }
}
