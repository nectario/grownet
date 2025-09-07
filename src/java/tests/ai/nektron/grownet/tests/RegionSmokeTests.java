package ai.nektron.grownet.tests;

import ai.nektron.grownet.Region;
import ai.nektron.grownet.metrics.RegionMetrics;
import org.junit.jupiter.api.Test;

import java.util.List;
import java.util.Random;

import static org.junit.jupiter.api.Assertions.*;

final class RegionSmokeTests {

    @Test
    void scalarTickAndPrune() {
        Region region = new Region("vision");

        int l0 = region.addLayer(40, 8, 4);
        int l1 = region.addLayer(30, 6, 3);

        // Bind an external input to the first layer
        region.bindInput("pixels", List.of(l0));

        // Random forward wiring and a tiny feedback trickle
        region.connectLayers(l0, l1, 0.10, /*feedback=*/false);
        region.connectLayers(l1, l0, 0.01, /*feedback=*/true);

        Random rng = new Random(1234);
        RegionMetrics last = null;
        for (int step = 0; step < 200; ++step) {
            last = region.tick("pixels", rng.nextDouble());
        }
        assertNotNull(last, "metrics should be returned");
        assertTrue(last.getTotalSlots() >= 0 && last.getTotalSynapses() >= 0, "metrics must be sane");

        // Prune weak/stale; just check that it doesn't throw and returns a summary.
        Region.PruneSummary p = region.prune(10_000, 0.05);
        assertNotNull(p);
        assertTrue(p.prunedSynapses >= 0);
    }

    @Test
    void tickWithoutEdgeThrows() {
        Region r = new Region("dbg");
        int l0 = r.addLayer(1, 0, 0);
        assertThrows(IllegalArgumentException.class, () -> r.tick("x", 0.5));
    }

    @Test
    void tick2DNeeds2DEdge() {
        Region r = new Region("dbg");
        int l0 = r.addLayer(1, 0, 0);
        r.bindInput("pixels", List.of(l0)); // scalar edge
        assertThrows(IllegalArgumentException.class,
                () -> r.tick2D("pixels", new double[][] {{1,0},{0,1}}));
    }

    @Test
    void scalarAnd2DWorkWhenBound() {
        Region r = new Region("dbg");
        int l0 = r.addLayer(1, 0, 0);
        r.bindInput("x", List.of(l0));
        assertEquals(1, r.tick("x", 0.42).getDeliveredEvents());

        int l1 = r.addLayer(1, 0, 0);
        r.bindInput2D("img", 2, 2, 1.0, 0.01, List.of(l1));
        assertEquals(1, r.tick2D("img", new double[][]{{1,0},{0,1}}).getDeliveredEvents());
    }

}
