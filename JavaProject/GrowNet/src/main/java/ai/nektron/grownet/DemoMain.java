package ai.nektron.grownet;

import java.util.Arrays;

/** Simple demo wiring and tick loop. */
public class DemoMain {
    public static void main(String[] args) {
        Region region = new Region("V1-lite");

        int l0 = region.addLayer(8, 2, 1);
        int l1 = region.addLayer(12, 3, 2);

        // Intra-layer random wiring
        region.getLayers().get(l0).wireRandomFeedforward(0.10);
        region.getLayers().get(l0).wireRandomFeedback(0.05);
        region.getLayers().get(l1).wireRandomFeedforward(0.10);

        // Inter-layer projection
        region.connectLayers(l0, l1, 0.15, false);

        // Bind external input to first layer
        region.bindInput("vision", Arrays.asList(l0));

        // Drive a simple ramp and print metrics
        for (int step = 0; step < 50; step++) {
            double value = (step % 10) * 0.1; // toy signal
            Region.RegionMetrics m = region.tick("vision", value);
            if (step % 10 == 0) {
                System.out.printf("step=%d  delivered=%d  slots=%d  synapses=%d%n",
                        step, m.deliveredEvents, m.totalSlots, m.totalSynapses);
            }
        }

        // Maintenance
        Region.PruneSummary pr = region.prune(10_000, 0.05, 10_000, 0.05);
        System.out.printf("Pruned synapses=%d  edges=%d%n", pr.prunedSynapses, pr.prunedEdges);
    }
}