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
        SlotConfig cfg = SlotConfig.fixed(10.0);  // 10% Δ bins
        int slotLimit = -1;                               // unlimited

        for (int i = 0; i < excitatoryCount; ++i) {
            Neuron n = new ExcitatoryNeuron("E" + i, bus, cfg, slotLimit);
            neurons.add(n);
        }
        for (int i = 0; i < inhibitoryCount; ++i) {
            Neuron n = new InhibitoryNeuron("I" + i, bus, cfg, slotLimit);
            neurons.add(n);
        }
        for (int i = 0; i < modulatoryCount; ++i) {
            Neuron n = new ModulatoryNeuron("M" + i, bus, cfg, slotLimit);
            neurons.add(n);
        }
    }

    // --------------------------------------------- accessors ------------------------------------------------

    public List<Neuron> neurons() { return neurons; }

    // ------------------------------------------ intra‑layer wiring ------------------------------------------

    /** Layer‑local fanout (demo‑level). */
    public void wireRandomFeedforward(double probability) {
        for (Neuron a : neurons) {
            for (Neuron b : neurons) {
                if (a == b) continue;
                if (rng.nextDouble() < probability) {
                    a.connect(b, /*feedback=*/false);
                }
            }
        }
    }

    public void wireRandomFeedback(double probability) {
        for (Neuron a : neurons) {
            for (Neuron b : neurons) {
                if (a == b) continue;
                if (rng.nextDouble() < probability) {
                    a.connect(b, /*feedback=*/true);
                }
            }
        }
    }

    // ------------------------------------------------ forward ------------------------------------------------

    /** Drive all neurons with a scalar value for this tick. */
    public void forward(double value) {
        for (Neuron n : neurons) {
            boolean fired = n.onInput(value);
            if (fired) {
                n.onOutput(value);
            }
        }
    }

    /** End‑of‑tick housekeeping: decay inhibition/modulation back toward neutral. */
    public void endTick() {
        bus.decay();
    }
}
