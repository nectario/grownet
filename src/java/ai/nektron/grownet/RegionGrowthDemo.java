package ai.nektron.grownet;

import ai.nektron.grownet.metrics.RegionMetrics;
import ai.nektron.grownet.growth.GrowthPolicy;

import java.util.List;

/**
 * RegionGrowthDemo — small smoke program to show automatic region growth.
 *
 * Wires Input2D -> Hidden -> Output2D, enables layer growth with aggressive
 * thresholds, then ticks a moving dot. Expect layer count to increase.
 */
public final class RegionGrowthDemo {
    private static double[][] frame(int h, int w, int step) {
        double[][] img = new double[h][w];
        int r = (step * 2) % h;
        int c = (step * 3) % w;
        img[r][c] = 1.0;
        return img;
    }

    public static void main(String[] args) {
        final int h = 8, w = 8;
        Region region = new Region("auto_grow_demo");

        int inIdx  = region.addInputLayer2D(h, w, 1.0, 0.01);
        int hidIdx = region.addLayer(16, 0, 0);
        int outIdx = region.addOutputLayer2D(h, w, 0.2);

        region.bindInput("pixels", List.of(inIdx));
        region.connectLayers(inIdx,  hidIdx, 0.50, false);
        region.connectLayers(hidIdx, outIdx, 0.20, false);

        // Aggressive policy so growth is easy to observe
        GrowthPolicy policy = new GrowthPolicy()
                .setEnableLayerGrowth(true)
                .setMaxLayers(16)
                .setAvgSlotsThreshold(0.0)
                .setLayerCooldownTicks(0);
        region.setGrowthPolicy(policy);

        int before = region.getLayers().size();
        for (int step = 0; step < 20; step++) {
            double[][] img = frame(h, w, step);
            RegionMetrics m = region.tick2D("pixels", img);
            if ((step + 1) % 5 == 0) {
                System.out.printf("[%02d] delivered=%d layers=%d%n",
                        step + 1,
                        m.getDeliveredEvents(),
                        region.getLayers().size());
            }
        }
        int after = region.getLayers().size();
        System.out.printf("Layers before=%d after=%d (growth %s)\n",
                before, after, (after > before ? "YES" : "NO"));
    }
}

