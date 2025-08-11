package ai.nektron.grownet;

import ai.nektron.grownet.SlotPolicyConfig;

import java.util.*;
import java.util.concurrent.ThreadLocalRandom;

/** A pool of neurons sharing a LateralBus. */
public final class Layer {
    protected SlotPolicyConfig slotPolicy = new SlotPolicyConfig();
    private final LateralBus bus = new LateralBus();
    private final List<Neuron> neurons = new ArrayList<>();

    public Layer(int excitCount, int inhibCount, int modCount) {
        for (int i = 0; i < excitCount; i++) neurons.add(new ExcitatoryNeuron("E" + i, bus));
        for (int i = 0; i < inhibCount; i++) neurons.add(new InhibitoryNeuron("I" + i, bus));
        for (int i = 0; i < modCount; i++) neurons.add(new ModulatoryNeuron("M" + i, bus));
    }

    public List<Neuron> getNeurons() { return neurons; }
    public LateralBus getBus() { return bus; }

    /** Randomly create excitatory connections between distinct neurons (no duplicates). */
    public void wireRandomFeedforward(double probability) {
        if (probability <= 0.0) return;
        ThreadLocalRandom rnd = ThreadLocalRandom.current();
        for (Neuron src : neurons) {
            for (Neuron dst : neurons) {
                if (src == dst || rnd.nextDouble() >= probability) continue;
                boolean exists = src.outgoing().stream().anyMatch(s -> s.target == dst);
                if (!exists) src.connect(dst, false);
            }
        }
    }

    /** Randomly add feedback edges (dst → src) tagged as feedback. */
    public void wireRandomFeedback(double probability) {
        if (probability <= 0.0) return;
        ThreadLocalRandom rnd = ThreadLocalRandom.current();
        for (Neuron src : neurons) {
            for (Neuron dst : neurons) {
                if (src == dst || rnd.nextDouble() >= probability) continue;
                boolean exists = dst.outgoing().stream().anyMatch(s -> s.target == src && s.feedback);
                if (!exists) dst.connect(src, true);
            }
        }
    }

    /** Advance one scalar value through the layer (all neurons). */
    public void forward(double value) {
        for (Neuron n : neurons) n.onInput(value);
        bus.decay();
        for (Neuron n : neurons) n.pruneSynapses(bus.currentStep(), 10_000, 0.05);
    }
}
