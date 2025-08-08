package ai.nektron.grownet;

import java.util.concurrent.ThreadLocalRandom;

public final class DemoMain {
    public static void main(String[] args) {
        Layer layer = new Layer(50, 10, 5);
        layer.wireRandomFeedforward(0.10);
        layer.wireRandomFeedback(0.01);

        ThreadLocalRandom rnd = ThreadLocalRandom.current();
        for (int i = 0; i < 5_000; i++) {
            layer.forward(rnd.nextDouble());  // synthetic stream
        }

        int totalSlots = layer.neurons().stream().mapToInt(n -> n.slots().size()).sum();
        int totalSynapses = layer.neurons().stream().mapToInt(n -> n.outgoing().size()).sum();
        System.out.printf("Finished. totalSlots=%d totalSynapses=%d%n", totalSlots, totalSynapses);
    }
}
