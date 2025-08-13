package ai.nektron.grownet;

/** Modulatory neuron scales learning when it fires. */
public class ModulatoryNeuron extends Neuron {
    private double modulationScale = 1.5; // > 1.0 speeds learning, < 1.0 slows

    public ModulatoryNeuron(String id, LateralBus bus) {
        super(id, bus);
    }

    public void setModulationScale(double scale) {
        modulationScale = Math.max(0.0, scale);
    }

    @Override
    protected void fire(double inputValue) {
        bus.pulseModulation(modulationScale);
        // Optional: also propagate locally
        super.fire(inputValue);
    }
}