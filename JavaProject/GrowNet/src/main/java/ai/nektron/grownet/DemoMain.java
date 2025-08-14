package ai.nektron.grownet;

import java.util.Arrays;
import ai.nektron.grownet.Region.Metrics;

/**
 * Simple demo wiring and tick loop.
 * Builds two layers, wires random feedforward/feedback inside each,
 * connects Layer0 -> Layer1, binds an external input port, then ticks.
 */
public final class DemoMain {
    public static void main(String[] args) {

        // Region
        Region region = new Region("v1_lite");

        // Layers (excitatory, inhibitory, modulatory)
        int inputLayerIndex  = region.addLayer(/*excitatory*/ 8,  /*inhibitory*/ 2, /*modulatory*/ 1);
        int hiddenLayerIndex = region.addLayer(/*excitatory*/ 12, /*inhibitory*/ 3, /*modulatory*/ 2);

        // Intra-layer random wiring
        region.layers().get(inputLayerIndex).wireRandomFeedforward(0.10);
        region.layers().get(inputLayerIndex).wireRandomFeedback(0.05);
        region.layers().get(hiddenLayerIndex).wireRandomFeedforward(0.10);

        // Inter-layer projection (feedforward only for this demo)
        region.connectLayers(inputLayerIndex, hiddenLayerIndex, 0.15, /*feedback=*/ false);

        // Bind external input to the first layer
        region.bindInput("vision", Arrays.asList(inputLayerIndex));

        // Drive a simple ramp signal and print metrics
        for (int step = 0; step < 50; step++) {
            double value = (step % 10) * 0.1;   // toy input signal in [0.0, 0.9]
            Metrics m = region.tick("vision", value);

            if ((step % 10) == 0) {
                System.out.printf(
                        "step=%02d  delivered=%d  slots=%d  synapses=%d%n",
                        step, m.deliveredEvents, m.totalSlots, m.totalSynapses
                );
            }
        }

        // Maintenance — prune weak/stale synapses (Java: 2-arg API)
        Region.PruneSummary pr = region.prune(
                /*synapseStaleWindow*/ 10_000L,
                /*synapseMinStrength*/ 0.05
        );

        // If your PruneSummary also carries prunedEdges, feel free to print it too.
        System.out.printf("Pruned synapses=%d%n", pr.prunedSynapses);
    }
}
