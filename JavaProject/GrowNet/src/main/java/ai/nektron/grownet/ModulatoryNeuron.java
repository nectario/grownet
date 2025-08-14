package ai.nektron.grownet;

public class ModulatoryNeuron extends Neuron {
    public ModulatoryNeuron(String id, LateralBus bus, SlotConfig cfg, int slotLimit) {
        super(id, bus, cfg, slotLimit);
    }
    @Override protected void fire(double inputValue) {
        bus.setModulation(1.5); // tune later
    }
}
