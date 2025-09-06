package ai.nektron.grownet;

/**
 * Input neuron: single-slot semantics with simple thresholded emission.
 * It still conforms to the unified onInput/onOutput contract.
 */
public final class InputNeuron extends Neuron {

    private final double gain;
    private final double epsilonFire;
    private double outputValue = 0.0;

    public InputNeuron(String id, LateralBus bus, double gain, double epsilonFire) {
        // Single-slot policy; slotLimit=1 to emphasize “no true slot learning” for inputs.
        super(id, bus, SlotConfig.singleSlot(), /*slotLimit*/ 1);
        this.gain = gain;
        this.epsilonFire = epsilonFire;
    }

    /** Drive with a scalar (e.g., pixel in [0, 1]); return true if it should emit. */
    @Override
    public boolean onInput(double value) {
        double amplified = gain * value;
        // Store so dashboards can read it even when not “firing”.
        this.outputValue = amplified;
        return Math.abs(amplified) >= epsilonFire;
    }

    /** For symmetry with the rest of the system; records last emitted value. */
    @Override
    public void onOutput(double amplitude) {
        this.outputValue = amplitude;
    }

    public double getOutputValue() { return outputValue; }
}
