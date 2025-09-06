package ai.nektron.grownet;

import java.util.List;

/**
 * Default spike semantics: propagate along outgoing synapses.
 * Each edge’s Weight is reinforced and thresholded; if it “fires”,
 * the target receives onInput with the same scalar value.
 */
public final class ExcitatoryNeuron extends Neuron {

    public ExcitatoryNeuron(String id, LateralBus bus, SlotConfig slotConfig, int slotLimit) {
        super(id, bus, slotConfig, slotLimit);
    }

    @Override
    protected void fire(double inputValue) {
        final List<Synapse> edges = getOutgoing();
        final double mod = getBus().getModulationFactor();
        final long   step = getBus().getCurrentStep();

        for (Synapse s : edges) {
            Weight w = s.getWeight();

            // local learning on the edge (+ neuromodulation)
            w.reinforce(mod);

            // bookkeeping for staleness pruning
            s.setLastStep(step);

            // only transmit if the edge’s compartment would fire
            if (w.updateThreshold(inputValue)) {
                Neuron child = s.getTarget();
                if (child != null) {
                    child.onInput(inputValue);
                }
            }
        }
    }
}
