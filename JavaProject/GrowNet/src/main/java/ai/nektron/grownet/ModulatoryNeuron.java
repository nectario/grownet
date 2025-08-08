package ai.nektron.grownet;

/** Emits a modulatory pulse (scales learning rate this tick). */
public final class ModulatoryNeuron extends Neuron {
    public ModulatoryNeuron(String neuronId, LateralBus bus) { super(neuronId, bus); }

    @Override public void fire(double inputValue) {
        bus.setModulationFactor(1.5);   // kappa; tune later
    }
}
