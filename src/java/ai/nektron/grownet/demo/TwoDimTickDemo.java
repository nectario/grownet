package ai.nektron.grownet.demo;

import ai.nektron.grownet.Region;
import ai.nektron.grownet.metrics.RegionMetrics;

import java.util.Arrays;

/**
 * Minimal 2D tick demo to step through windowed wiring and event delivery.
 *
 * Suggested breakpoints for step‑through debugging:
 *  - Region.connectLayersWindowed(...)   // window origins, center mapping, unique sources
 *  - Region.tick2D(...)                  // per‑tick orchestration
 *  - InputLayer2D.forwardImage(...)      // drives input neurons row‑major
 *  - Tract.onSourceFiredIndex(...)       // routes source pixel → center output neuron
 *  - OutputLayer2D.propagateFrom(...)    // unified onInput/onOutput for outputs
 */
public final class TwoDimTickDemo {
    public static void main(String[] args) {
        final int height = 8;
        final int width  = 8;

        Region region = new Region("two-d-tick-demo");

        // Build a simple 2D pipeline: Input2D → Output2D, windowed wiring (3x3, SAME)
        int inputIndex  = region.addInputLayer2D(height, width, /*gain=*/1.0, /*epsilonFire=*/0.01);
        int outputIndex = region.addOutputLayer2D(height, width, /*smoothing=*/0.0);

        int uniqueSources = region.connectLayersWindowed(
                inputIndex, outputIndex,
                /*kernelH*/3, /*kernelW*/3,
                /*strideH*/1, /*strideW*/1,
                /*padding*/"same",
                /*feedback*/false);
        System.out.println("unique_sources=" + uniqueSources);

        // Bind the input port to the InputLayer2D edge; tick with a bright pixel
        region.bindInput2D("pixels", height, width, 1.0, 0.01, Arrays.asList(inputIndex));

        double[][] frame = new double[height][width];
        frame[3][4] = 1.0;   // bright pixel near the center

        // Breakpoint here to step through Region.tick2D → forwardImage → tract delivery → output update
        RegionMetrics m1 = region.tick2D("pixels", frame);
        System.out.printf("tick#1 delivered=%d slots=%d synapses=%d%n",
                m1.delivered_events, m1.total_slots, m1.total_synapses);

        // Move the bright pixel; this exercises a different (source → center) mapping
        frame[3][4] = 0.0;
        frame[5][6] = 1.0;
        RegionMetrics m2 = region.tick2D("pixels", frame);
        System.out.printf("tick#2 delivered=%d slots=%d synapses=%d%n",
                m2.delivered_events, m2.total_slots, m2.total_synapses);
    }
}

