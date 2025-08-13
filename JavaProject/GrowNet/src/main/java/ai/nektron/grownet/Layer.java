package ai.nektron.grownet;

import java.util.*;

/** A collection of neurons sharing a LateralBus and intra-layer wiring. */
public class Layer {
    private final LateralBus bus = new LateralBus();
    private final List<Neuron> neurons = new ArrayList<>();
    private final Random random = new Random();

    public Layer(int excitatoryCount, int inhibitoryCount, int modulatoryCount) {
        for (int i = 0; i < excitatoryCount; i++) neurons.add(new ExcitatoryNeuron("E" + i, bus));
        for (int i = 0; i < inhibitoryCount; i++) neurons.add(new InhibitoryNeuron("I" + i, bus));
        for (int i = 0; i < modulatoryCount; i++) neurons.add(new ModulatoryNeuron("M" + i, bus));
    }

    public LateralBus getBus() { return bus; }
    public List<Neuron> getNeurons() { return neurons; }

    /** Random intra-layer feed-forward connections (excluding self). */
    public void wireRandomFeedforward(double probability) {
        if (probability <= 0.0) return;
        int n = neurons.size();
        for (int s = 0; s < n; s++) {
            for (int t = 0; t < n; t++) {
                if (s == t) continue;
                if (random.nextDouble() < probability) {
                    neurons.get(s).connect(neurons.get(t), false);
                }
            }
        }
    }

    /** Random intra-layer feedback connections (reverse direction). */
    public void wireRandomFeedback(double probability) {
        if (probability <= 0.0) return;
        int n = neurons.size();
        for (int s = 0; s < n; s++) {
            for (int t = 0; t < n; t++) {
                if (s == t) continue;
                if (random.nextDouble() < probability) {
                    neurons.get(t).connect(neurons.get(s), true);
                }
            }
        }
    }

    /** Deliver a scalar input to all neurons and perform maintenance. */
    public void forward(double value) {
        for (Neuron neuron : neurons) neuron.onInput(value);
        bus.decay();
        for (Neuron neuron : neurons) neuron.pruneSynapses(bus.getCurrentStep(), 10_000, 0.05);
    }
}