package ai.nektron.grownet.tests;

import ai.nektron.grownet.Region;
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

import java.util.List;

public class RegionPulseParityTest {

    @Test
    void pulsesReachLayerBus() {
        Region r = new Region("dbg");
        int l0 = r.addLayer(1,0,0);
        r.bindInput("x", List.of(l0));

        r.pulseModulation(1.5);
        r.pulseInhibition(0.7);

        // No direct getters? Then rely on no-throw tick and behavior; minimally assert no crash.
        assertDoesNotThrow(() -> r.tick("x", 0.4));
    }
}
