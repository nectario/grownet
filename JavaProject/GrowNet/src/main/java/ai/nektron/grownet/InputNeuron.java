package ai.nektron.grownet;

/** Input neuron with a single effective slot; acts excitatorily downstream. */
public class InputNeuron extends Neuron {
    public InputNeuron(String id, LateralBus bus) { super(id, bus); }

    @Override
    protected Weight selectSlot(double inputValue) {
        // Always use slot 0
        Weight w = slots.get(0);
        if (w == null) {
            w = new Weight();
            slots.put(0, w);
        }
        return w;
    }
    // fire() inherited (excitatory)
}