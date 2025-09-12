package ai.nektron.grownet.tests;

import ai.nektron.grownet.Region;
import ai.nektron.grownet.metrics.RegionMetrics;
import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.*;

public class SpatialMetricsPublicTest {

    @Test
    public void computeSpatialMetricsFromImage() {
        Region region = new Region("spatial-metrics");
        double[][] img = new double[][]{
                {0.0, 1.0, 0.0},
                {0.0, 0.0, 0.0}
        };
        RegionMetrics m = region.computeSpatialMetrics(img, /*preferOutput*/ false);
        assertEquals(1L, m.getActivePixels());
        assertEquals(0.0, m.getCentroidRow(), 1e-12);
        assertEquals(1.0, m.getCentroidCol(), 1e-12);
        assertEquals(0, m.getBboxRowMin());
        assertEquals(0, m.getBboxRowMax());
        assertEquals(1, m.getBboxColMin());
        assertEquals(1, m.getBboxColMax());
    }
}

