package ai.nektron.grownet;

/** Inhibitory neuron emits an inhibitory pulse on the bus when it fires. */
public class InhibitoryNeuron extends Neuron {
    private double inhibitionPulse = 0.7; // multiply strengths by 0.7 for one tick

    public InhibitoryNeuron(String id, LateralBus bus) {
        super(id, bus);
    }

    public void setInhibitionPulse(double value) {
        inhibitionPulse = MathUtils.clamp(value, 0.0, 1.0);
    }

    @Override
    protected void fire(double inputValue) {
        bus.pulseInhibition(inhibitionPulse);
        // Still allow local outgoing (rare), or comment out to disable propagation:
        super.fire(inputValue);
    }
}