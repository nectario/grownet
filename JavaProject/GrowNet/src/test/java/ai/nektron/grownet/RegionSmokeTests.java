package ai.nektron.grownet;

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
        assertTrue(last.totalSlots >= 0 && last.totalSynapses >= 0, "metrics must be sane");

        // Prune weak/stale; just check that it doesn't throw and returns a summary.
        Region.PruneSummary p = region.prune(10_000, 0.05);
        assertNotNull(p);
        assertTrue(p.prunedSynapses >= 0);
    }
}
