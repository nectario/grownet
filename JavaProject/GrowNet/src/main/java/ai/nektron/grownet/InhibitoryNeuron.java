package ai.nektron.grownet;

/**
 * Emits a lateral inhibition pulse onto the bus.
 * By default it does NOT propagate to its edges (pure inhibitory role).
 */
public final class InhibitoryNeuron extends Neuron {
    private double gamma = 0.70;   // inhibition strength (0..1), tweak later

    public InhibitoryNeuron(String id, LateralBus bus, SlotConfig slotConfig, int slotLimit) {
        super(id, bus, slotConfig, slotLimit);
    }

    public double getGamma() { return gamma; }
    public void setGamma(double value) { gamma = value; }

    @Override
    protected void fire(double inputValue) {
        bus().setInhibitionFactor(gamma);
        // If you later want mixed behavior, you could also call super.fire(inputValue)
        // to both inhibit and propagate. For now we keep the role pure and simple.
    }
}
