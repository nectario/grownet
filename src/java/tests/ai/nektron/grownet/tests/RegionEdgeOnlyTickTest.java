package ai.nektron.grownet.tests;

import ai.nektron.grownet.Region;
import ai.nektron.grownet.metrics.RegionMetrics;
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

import java.util.List;

/**
 * Edge-only delivery semantics: a scalar tick drives the bound edge exactly once; 
 * deliveredEvents should equal 1 per port event.
 */
public class RegionEdgeOnlyTickTest {

    @Test
    void tickWithoutEdgeThrows() {
        Region r = new Region("dbg");
        int l0 = r.addLayer(1,0,0);
        // No bindInput yet
        assertThrows(IllegalArgumentException.class, () -> r.tick("x", 0.42));
    }

    @Test
    void tickViaEdgeDeliversOnce() {
        Region r = new Region("dbg");
        int l0 = r.addLayer(1,0,0);
        r.bindInput("x", List.of(l0));
        RegionMetrics m = r.tick("x", 0.42);
        assertEquals(1, m.getDeliveredEvents());
        assertTrue(m.getTotalSlots() >= 0);
        assertTrue(m.getTotalSynapses() >= 0);
    }
}
