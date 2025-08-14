package ai.nektron.grownet;

import java.util.*;

public final class Layer {
    private final LateralBus bus = new LateralBus();
    private final List<Neuron> neurons = new ArrayList<>();

    public Layer(int excitatoryCount, int inhibitoryCount, int modulatoryCount, SlotConfig cfg) {
        for (int i = 0; i < excitatoryCount; i++)
            neurons.add(new ExcitatoryNeuron("E"+i, bus, cfg, -1));
        for (int i = 0; i < inhibitoryCount; i++)
            neurons.add(new InhibitoryNeuron("I"+i, bus, cfg, -1));
        for (int i = 0; i < modulatoryCount; i++)
            neurons.add(new ModulatoryNeuron("M"+i, bus, cfg, -1));
    }

    public void forward(double value) {
        for (Neuron n : neurons) { n.onInput(value); }
    }

    public void decay() { bus.decay(); }
    public List<Neuron> neurons() { return neurons; }
    public LateralBus bus() { return bus; }
}
