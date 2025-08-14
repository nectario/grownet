package ai.nektron.grownet;

public class ExcitatoryNeuron extends Neuron {
    public ExcitatoryNeuron(String id, LateralBus bus, SlotConfig cfg, int slotLimit) {
        super(id, bus, cfg, slotLimit);
    }
    @Override protected void fire(double inputValue) {
        // Layer/Tract handles routing; keep hook for symmetry
    }
}
