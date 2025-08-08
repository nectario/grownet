package ai.nektron.grownet;

/** Emits an inhibitory pulse (scales learning/strength this tick). */
public final class InhibitoryNeuron extends Neuron {
    public InhibitoryNeuron(String neuronId, LateralBus bus) { super(neuronId, bus); }

    @Override public void fire(double inputValue) {
        bus.setInhibitionFactor(0.7);   // gamma; tune later
    }
}
