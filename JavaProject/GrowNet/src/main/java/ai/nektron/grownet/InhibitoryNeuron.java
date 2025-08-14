package ai.nektron.grownet;

public class InhibitoryNeuron extends Neuron {
    public InhibitoryNeuron(String id, LateralBus bus, SlotConfig cfg, int slotLimit) {
        super(id, bus, cfg, slotLimit);
    }
    @Override protected void fire(double inputValue) {
        bus.setInhibition(0.7); // tune later
    }
}
