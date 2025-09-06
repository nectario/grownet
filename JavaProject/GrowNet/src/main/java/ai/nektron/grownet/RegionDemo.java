package ai.nektron.grownet;

import ai.nektron.grownet.metrics.RegionMetrics;

import java.util.List;
import java.util.Random;

public final class RegionDemo {

    public static void main(String[] args) {
        Region region = new Region("vision");

        // Two simple layers
        int l0 = region.addLayer(40, 8, 4);
        int l1 = region.addLayer(30, 6, 3);

        // Bind an external input port to the first layer
        region.bindInput("pixels", List.of(l0));

        // Random wiring: feedforward + a tiny feedback trickle
        region.connectLayers(l0, l1, 0.10, false);
        region.connectLayers(l1, l0, 0.01, true);

        // Drive with a scalar stream and print metrics
        Random rng = new Random(1234);
        for (int step = 1; step <= 2000; step++) {
            RegionMetrics m = region.tick("pixels", rng.nextDouble());  // <-- fixed call

            if (step % 200 == 0) {
                System.out.printf(
                        "[step %d] delivered=%d slots=%d syn=%d%n",
                        step, m.getDeliveredEvents(), m.getTotalSlots(), m.getTotalSynapses()
                );
            }
        }

        // Maintenance: prune weak/stale synapses (2-arg API)
        Region.PruneSummary p = region.prune(10_000, 0.05);              // <-- fixed call
        System.out.printf("Prune summary: prunedSynapses=%d prunedEdges=%d%n",
                p.prunedSynapses, p.prunedEdges);
    }
}
