package ai.nektron.grownet;

import java.util.*;

/**
 * A mixed‑type population (excitatory, inhibitory, modulatory) that shares a lateral bus.
 */
public class Layer {

    private final List<Neuron> neurons = new ArrayList<>();
    private final LateralBus bus = new LateralBus();
    private final Random rng = new Random(1234);

    public Layer(int excitatoryCount, int inhibitoryCount, int modulatoryCount) {
        // Default slot policy for this demo layer.
        SlotConfig cfg = SlotConfig.fixed(10.0);   // 10% Δ bins
        int slotLimit = -1;                        // unlimited

        for (int i = 0; i < excitatoryCount; ++i) {
            Neuron neuron = new ExcitatoryNeuron("E" + i, bus, cfg, slotLimit);
            neurons.add(neuron);
        }
        for (int i = 0; i < inhibitoryCount; ++i) {
            Neuron neuron = new InhibitoryNeuron("I" + i, bus, cfg, slotLimit);
            neurons.add(neuron);
        }
        for (int i = 0; i < modulatoryCount; ++i) {
            Neuron neuron = new ModulatoryNeuron("M" + i, bus, cfg, slotLimit);
            neurons.add(neuron);
        }
    }

    // --------------------------------------------- accessors ------------------------------------------------

    public List<Neuron> getNeurons() { return neurons; }
    public LateralBus getBus() { return bus; }

    // ------------------------------------------ intra‑layer wiring ------------------------------------------

    /** Layer‑local fanout (demo‑level). */
    public void wireRandomFeedforward(double probability) {
        for (Neuron srcNeuron : neurons) {
            for (Neuron dstNeuron : neurons) {
                if (srcNeuron == dstNeuron) continue;
                if (rng.nextDouble() < probability) {
                    srcNeuron.connect(dstNeuron, /*feedback=*/false);
                }
            }
        }
    }

    public void wireRandomFeedback(double probability) {
        for (Neuron srcNeuron : neurons) {
            for (Neuron dstNeuron : neurons) {
                if (srcNeuron == dstNeuron) continue;
                if (rng.nextDouble() < probability) {
                    srcNeuron.connect(dstNeuron, /*feedback=*/true);
                }
            }
        }
    }

    // ------------------------------------------------ forward ------------------------------------------------

    /** Drive all neurons with a scalar value for this tick. */
    public void forward(double value) {
        for (Neuron neuron : neurons) {
            boolean fired = neuron.onInput(value);
            if (fired) {
                neuron.onOutput(value);
            }
        }
    }

    /**
     * Optional helper used by shape‑aware layers (e.g., OutputLayer2D).
     * Default behaviour: route {@code value} to the N‑th neuron and apply the unified onInput/onOutput contract.
     * NOTE: The inter‑layer wiring (`Tract`) does NOT call this; it delivers directly to target neurons.
     * This method exists so specialized layers can @Override it for local bookkeeping.
     */
    public void propagateFrom(int sourceIndex, double value) {
        if (sourceIndex < 0 || sourceIndex >= neurons.size()) return;
        Neuron neuron = neurons.get(sourceIndex);
        boolean fired = neuron.onInput(value);
        if (fired) neuron.onOutput(value);
    }

    /** End‑of‑tick housekeeping: decay inhibition/modulation back toward neutral. */
    public void endTick() {
        bus.decay();
    }
}
