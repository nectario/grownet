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

    public boolean onRoutedEvent(double value, double modulation, double inhibition) {
        Weight slot = getSlots().get(0);
        slot.reinforce(modulation, inhibition);
        boolean fired = slot.updateThreshold(value);
        setFiredLast(fired);
        setLastInputValue(value);
        if (fired) {
            accumulatedSum  += value;
            accumulatedCount += 1;
        }
        return fired;
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
