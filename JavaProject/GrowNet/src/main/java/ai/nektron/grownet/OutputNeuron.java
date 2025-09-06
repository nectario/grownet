package ai.nektron.grownet;

public class OutputNeuron extends Neuron {
    /** Value emitted during the current tick (transient). */
    private double lastEmitted = 0.0;

    /** Snapshot captured at endTick() (stable until next endTick). */
    private double outputValue = 0.0;

    public OutputNeuron(String id, LateralBus bus, SlotConfig cfg) {
        // single-slot sink; no slot learning (slot limit = 1)
        super(id, bus, cfg, 1);
    }

    @Override
    public boolean onInput(double value) {
        // Ensure the single slot exists
        Weight slot = slots.getOrDefault(0, new Weight());
        slots.putIfAbsent(0, slot);

        // Local learning scaled by the region/layer bus
        slot.reinforce(bus.getModulationFactor());

        // Adaptive threshold; decide whether we fired
        boolean fired = slot.updateThreshold(value);
        if (fired) {
            onOutput(value);
        }

        // Bookkeeping for neuron_value() style helpers, etc.
        haveLastInput  = true;
        lastInputValue = value;
        return fired;
    }

    @Override
    public void onOutput(double amplitude) {
        // Record what we emitted this tick (will be snapshotted in endTick).
        lastEmitted = amplitude;
    }

    /** Snapshot the last emitted value and clear the transient for the next tick. */
    public void endTick() {
        outputValue = lastEmitted;
        lastEmitted = 0.0;   // so non-firing neurons show 0 on the next frame
    }

    /** Value that OutputLayer2D should write into the frame. */
    public double getOutputValue() {
        return outputValue;
    }
}
