package ai.nektron.grownet;

import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.ThreadLocalRandom;

/**
 * A pool of neurons sharing a LateralBus.
 * Contract: when a neuron fires, call onOutput(value) first, then propagate.
 * Output neurons are sinks/actuators: they must not create new events.
 */
public class Layer {

    private final LateralBus bus = new LateralBus();
    private final List<Neuron> neurons = new ArrayList<>();

    public Layer(int excitatoryCount, int inhibitoryCount, int modulatoryCount) {
        for (int i = 0; i < excitatoryCount; i++) neurons.add(new ExcitatoryNeuron("E" + i, bus));
        for (int i = 0; i < inhibitoryCount; i++) neurons.add(new InhibitoryNeuron("I" + i, bus));
        for (int i = 0; i < modulatoryCount; i++) neurons.add(new ModulatoryNeuron("M" + i, bus));
    }

    public List<Neuron> getNeurons() { return neurons; }

    public LateralBus getBus() { return bus; }

    // ---------- Wiring (intra-layer) ----------

    /**
     * Randomly wire feedforward-style edges between distinct neurons (no duplicates).
     * Edges created here are NOT marked as feedback.
     */
    public void wireRandomFeedforward(double probability) {
        if (probability <= 0.0) return;

        ThreadLocalRandom rnd = ThreadLocalRandom.current();
        for (int si = 0; si < neurons.size(); si++) {
            Neuron src = neurons.get(si);
            for (int di = 0; di < neurons.size(); di++) {
                if (si == di) continue;
                Neuron dst = neurons.get(di);

                if (rnd.nextDouble() >= probability) continue;

                boolean exists = src.getOutgoing().stream()
                        .anyMatch(s -> s.getTarget() == dst && !s.isFeedback());
                if (!exists) {
                    src.connect(dst, /*feedback*/ false);
                }
            }
        }
    }

    /**
     * Randomly add edges tagged as feedback (reverse-looking links), avoiding duplicates.
     */
    public void wireRandomFeedback(double probability) {
        if (probability <= 0.0) return;

        ThreadLocalRandom rnd = ThreadLocalRandom.current();
        for (int si = 0; si < neurons.size(); si++) {
            Neuron src = neurons.get(si);
            for (int di = 0; di < neurons.size(); di++) {
                if (si == di) continue;
                Neuron dst = neurons.get(di);

                if (rnd.nextDouble() >= probability) continue;

                // feedback edge goes from dst -> src, marked as feedback
                boolean exists = dst.getOutgoing().stream()
                        .anyMatch(s -> s.getTarget() == src && s.isFeedback());
                if (!exists) {
                    dst.connect(src, /*feedback*/ true);
                }
            }
        }
    }

    // ---------- Phase A: scalar injection into this layer ----------

    /**
     * Drive the entire layer with a scalar input.
     * If a neuron fires, we call onOutput(value) and then let it propagate.
     */
    public void forward(double value) {
        for (Neuron n : neurons) {
            boolean fired = n.onInput(value);
            if (fired) {
                // Unified hook — must happen before any propagation.
                n.onOutput(value);

                // Relay: hidden/input neurons may propagate; outputs are sinks (their fire() is a no-op).
                n.fire(value);
            }
        }
    }

    // ---------- Maintenance helpers ----------

    /**
     * Prune outgoing synapses that are both stale and weak (per-neuron).
     * Called by Region.prune(...). Kept here as a convenience pass.
     */
    public int pruneSynapses(long currentStep, long staleWindow, double minStrength) {
        int pruned = 0;
        for (Neuron n : neurons) {
            int before = n.getOutgoing().size();
            n.pruneSynapses(currentStep, staleWindow, minStrength);
            pruned += before - n.getOutgoing().size();
        }
        return pruned;
    }
}
