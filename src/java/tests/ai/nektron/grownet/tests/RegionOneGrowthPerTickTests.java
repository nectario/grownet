package ai.nektron.grownet.tests;

import ai.nektron.grownet.Region;
import ai.nektron.grownet.growth.GrowthPolicy;
import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.*;

public class RegionOneGrowthPerTickTests {

    @Test
    public void growsAtMostOneLayerPerTick() {
        Region region = new Region("one-per-tick");
        int in = region.addInputLayer2D(4,4,1.0,0.01);
        int hid = region.addLayer(6,0,0);
        region.connectLayersWindowed(in, hid, 2,2,1,1, "valid", false);
        region.bindInput2D("img", 4,4,1.0,0.01, java.util.List.of(in));

        GrowthPolicy policy = new GrowthPolicy()
                .setEnableLayerGrowth(true)
                .setMaxLayers(64)
                .setAvgSlotsThreshold(0.0)
                .setLayerCooldownTicks(0);
        region.setGrowthPolicy(policy);

        int prevLayers = region.getLayers().size();
        for (int step = 0; step < 5; ++step) {
            region.tick2D("img", new double[][]{
                    {1.0, 1.0, 1.0, 1.0},
                    {1.0, 1.0, 1.0, 1.0},
                    {1.0, 1.0, 1.0, 1.0},
                    {1.0, 1.0, 1.0, 1.0}
            });
            int nowLayers = region.getLayers().size();
            int delta = nowLayers - prevLayers;
            assertTrue(delta == 0 || delta == 1, "at most one growth per tick");
            prevLayers = nowLayers;
        }
    }
}

