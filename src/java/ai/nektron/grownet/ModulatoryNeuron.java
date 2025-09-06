package ai.nektron.grownet;

/**
 * Emits a neuromodulatory pulse that scales learning rate during this tick.
 * (e.g., dopamine-like “surprise” signal).
 */
public final class ModulatoryNeuron extends Neuron {
    private double kappa = 1.50;   // learning-rate multiplier, tweak later

    public ModulatoryNeuron(String id, LateralBus bus, SlotConfig slotConfig, int slotLimit) {
        super(id, bus, slotConfig, slotLimit);
    }

    public double getKappa() { return kappa; }
    public void setKappa(double value) { kappa = value; }

    @Override
    protected void fire(double inputValue) {
        getBus().setModulationFactor(kappa);

        // As with InhibitoryNeuron, we keep the role pure by default (no edge propagation).
    }
}
