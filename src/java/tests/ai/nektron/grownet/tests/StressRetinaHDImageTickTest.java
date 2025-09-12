package ai.nektron.grownet.tests;

import ai.nektron.grownet.Region;
import ai.nektron.grownet.metrics.RegionMetrics;
import ai.nektron.grownet.preset.TopographicConfig;
import ai.nektron.grownet.preset.TopographicWiring;
import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.*;

/**
 * Retina-style (topographic) wiring stress: InputLayer2D → OutputLayer2D with SAME padding, kernel 7x7,
 * stride 1 on a 1920x1080 image; measure one 2D tick duration.
 */
public class StressRetinaHDImageTickTest {

    @Test
    public void hdImageRetinaSingleTickTiming() {
        final int height = 1080;
        final int width  = 1920;

        Region region = new Region("stress-retina-hd");
        int inputLayerIndex  = region.addInputLayer2D(height, width, 1.0, 0.01);
        int out = region.addOutputLayer2D(height, width, 0.0);

        TopographicConfig cfg = new TopographicConfig()
                .setKernel(7,7)
                .setStride(1,1)
                .setPadding("same")
                .setWeightMode("gaussian")
                .setNormalizeIncoming(true);
        int unique = TopographicWiring.connectLayersTopographic(region, inputLayerIndex, out, cfg);
        assertTrue(unique > 0);

        region.bindInput2D("img", height, width, 1.0, 0.01, java.util.List.of(inputLayerIndex));

        // Build frame with a diagonal
        double[][] frame = new double[height][width];
        for (int r = 0; r < height; ++r) {
            frame[r][r % width] = 1.0;
        }

        // Warm-up
        region.tick2D("img", frame);

        long t0 = System.nanoTime();
        RegionMetrics metrics = region.tick2D("img", frame);
        long dtMs = (System.nanoTime() - t0) / 1_000_000L;
        System.out.println("[JAVA] Retina HD 1920x1080 tick took ~" + dtMs + " ms; deliveredEvents=" + metrics.getDeliveredEvents());
        assertEquals(1, metrics.getDeliveredEvents());
    }
}
