package ai.nektron.grownet;

import java.util.concurrent.ThreadLocalRandom;

public final class DemoMain {
    public static void main(String[] args) {
        Layer layer = new Layer(50, 10, 5);
        layer.wireRandomFeedforward(0.10);
        layer.wireRandomFeedback(0.01);

        ThreadLocalRandom rnd = ThreadLocalRandom.current();

        for (int i = 0; i < 5_000; i++) {
            layer.forward(rnd.nextDouble());
            if ((i + 1) % 500 == 0) {
                double avg = layer.getNeurons().stream()
                        .mapToDouble(n -> n.neuronValue("readiness")).average().orElse(0.0);
                double max = layer.getNeurons().stream()
                        .mapToDouble(n -> n.neuronValue("readiness")).max().orElse(0.0);
                System.out.printf("[tick %d] readiness avg=%.3f max=%.3f%n", i + 1, avg, max);
            }
        }

        int totalSlots = layer.getNeurons().stream().mapToInt(n -> n.slots().size()).sum();
        int totalSynapses = layer.getNeurons().stream().mapToInt(n -> n.outgoing().size()).sum();
        System.out.printf("Finished. totalSlots=%d totalSynapses=%d%n", totalSlots, totalSynapses);
    }
}
