package tests.ai.nektron.grownet.tests;

import ai.nektron.grownet.Region;
import ai.nektron.grownet.growth.GrowthPolicy;
import org.junit.jupiter.api.Test;

import java.util.List;

import static org.junit.jupiter.api.Assertions.assertTrue;

public class RegionGrowthTest {

    @Test
    public void testRegionAddsLayerUnderPressure() {
        final int h = 4, w = 4;
        Region region = new Region("rg");

        int inIdx  = region.addInputLayer2D(h, w, 1.0, 0.01);
        int hidIdx = region.addLayer(6, 0, 0);
        region.connectLayersWindowed(inIdx, hidIdx, 2, 2, 1, 1, "valid", false);
        region.bindInput("img", List.of(inIdx));

        GrowthPolicy policy = new GrowthPolicy()
                .setEnableLayerGrowth(true)
                .setMaxLayers(32)
                .setAvgSlotsThreshold(0.0)
                .setLayerCooldownTicks(0);
        region.setGrowthPolicy(policy);

        int before = region.getLayers().size();
        // Drive a few frames
        double[][] f1 = new double[][]{{0,1,0,0},{0,0,0,0},{0,0,0,0},{0,0,0,0}};
        double[][] f2 = new double[][]{{0,0,1,0},{0,0,0,0},{0,0,0,0},{0,0,0,0}};
        double[][] f3 = new double[][]{{0,0,0,1},{0,0,0,0},{0,0,0,0},{0,0,0,0}};
        region.tick2D("img", f1);
        region.tick2D("img", f2);
        region.tick2D("img", f3);

        int after = region.getLayers().size();
        assertTrue(after > before, "expected layer count to increase");
    }
}
