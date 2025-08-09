package ai.nektron.grownet;

public class OutputNeuron extends Neuron {
    private final double smoothing;
    private double accumulatedSum = 0.0;
    private int    accumulatedCount = 0;
    private double outputValue = 0.0;

    public OutputNeuron(String name, double smoothing) {
        super(name);
        this.smoothing = smoothing;
        getSlots().computeIfAbsent(0, k -> new Weight());
    }

    /** Unified onInput: gate + reinforcement; does NOT fire/propagate. */
    public boolean onInput(double value, double modulation, double inhibition) {
        Weight slot = getSlots().get(0);
        slot.reinforce(modulation, inhibition);
        boolean fired = slot.updateThreshold(value);
        setFiredLast(fired);
        setLastInputValue(value);
        return fired;
    }

    /** Unified onOutput: accumulate contribution this tick. */
    @Override
    public void onOutput(double amplitude) {
        accumulatedSum  += amplitude;
        accumulatedCount += 1;
    }

    public void endTick() {
        if (accumulatedCount > 0) {
            double mean = accumulatedSum / accumulatedCount;
            outputValue = (1.0 - smoothing) * outputValue + smoothing * mean;
        }
        accumulatedSum = 0.0;
        accumulatedCount = 0;
    }

    public double getOutputValue() { return outputValue; }
}
