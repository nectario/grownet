package ai.nektron.grownet;

/** Output neuron captures the most recent emitted amplitude via onOutput(). */
public class OutputNeuron extends Neuron {
    private double lastEmittedValue = 0.0;

    public OutputNeuron(String id, LateralBus bus) { super(id, bus); }

    @Override
    public void onOutput(double amplitude) {
        lastEmittedValue = amplitude;
    }

    public double getLastEmittedValue() { return lastEmittedValue; }

    // As a sink, by default do not propagate further on fire; comment to enable fan-out.
    @Override
    protected void fire(double inputValue) {
        onOutput(inputValue);
    }
}