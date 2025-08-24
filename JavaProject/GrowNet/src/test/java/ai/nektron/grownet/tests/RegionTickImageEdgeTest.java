package ai.nektron.grownet.tests;

import ai.nektron.grownet.Region;
import ai.nektron.grownet.metrics.RegionMetrics;
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

import java.util.List;

public class RegionTickImageEdgeTest {

    @Test
    void tickImageRequires2DEdge() {
        Region r = new Region("dbg");
        int l0 = r.addLayer(1,0,0);
        // Wrong: scalar edge
        r.bindInput("pixels", List.of(l0));
        assertThrows(IllegalArgumentException.class, () -> r.tickImage("pixels", new double[2][2]));
    }

    @Test
    void tickImageWith2DEdge() {
        Region region = new Region("dbg");
        int l0 = region.addLayer(1,0,0);
        region.bindInput2D("pixels", 2, 2, /*gain=*/1.0, /*epsilonFire=*/0.01, List.of(l0));
        RegionMetrics m = region.tickImage("pixels", new double[][]{{1.0,0.0},{0.0,1.0}});
        assertEquals(1, m.getDeliveredEvents());
    }
}
