package ai.nektron.grownet.tests;

import ai.nektron.grownet.Region;
import ai.nektron.grownet.metrics.RegionMetrics;
import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.*;

/**
 * Stress test: drive a 1920x1080 frame through a Region and measure one 2D tick duration.
 * This is a functional smoke that prints timing; it does not assert a hard threshold to
 * avoid flakiness across environments.
 */
public class StressHDImageTickTest {

    @Test
    public void hdImageSingleTickTiming() {
        final int height = 1080;
        final int width  = 1920;

        // Build region with only an image input edge bound to the port (no extra wiring).
        Region region = new Region("stress-hd");
        region.bindInput2D("img", height, width, /*gain=*/1.0, /*epsilonFire=*/0.01,
                java.util.List.of());

        // Construct a simple frame with a diagonal pattern.
        double[][] frame = new double[height][width];
        for (int rowIndex = 0; rowIndex < height; ++rowIndex) {
            int colIndex = rowIndex % width;
            frame[rowIndex][colIndex] = 1.0;
        }

        // Warm-up tick to stabilize JIT/allocs
        region.tick2D("img", frame);

        long t0 = System.nanoTime();
        RegionMetrics metrics = region.tick2D("img", frame);
        long dtMs = (System.nanoTime() - t0) / 1_000_000L;

        System.out.println("[JAVA] HD 1920x1080 tick took ~" + dtMs + " ms; deliveredEvents=" + metrics.getDeliveredEvents());

        assertEquals(1, metrics.getDeliveredEvents(), "A single 2D tick should count as one delivered event");
    }
}
