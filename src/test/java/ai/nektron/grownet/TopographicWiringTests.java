package ai.nektron.grownet;

import ai.nektron.grownet.preset.TopographicConfig;
import ai.nektron.grownet.preset.TopographicWiring;
import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.*;

public class TopographicWiringTests {

    @Test
    public void uniqueSourceReturnAndNormalization() {
        Region region = new Region("topo-return");
        int src = region.addInputLayer2D(8, 8, 1.0, 0.01);
        int dst = region.addOutputLayer2D(8, 8, 0.0);
        TopographicConfig cfg = new TopographicConfig().setKernel(3,3).setPadding("same").setWeightMode("gaussian").setNormalizeIncoming(true);
        int unique = TopographicWiring.connectLayersTopographic(region, src, dst, cfg);
        assertEquals(64, unique);
        double[] sums = TopographicWiring.incomingSums(region, dst);
        for (double s : sums) {
            if (s > 0.0) assertTrue(Math.abs(s - 1.0) < 1e-6);
        }
    }
}

