package ai.nektron.grownet;

import java.util.List;
import java.util.Random;

public final class RegionDemo {
    public static void main(String[] args) {
        Region region = new Region("vision");
        int l0 = region.addLayer(40, 8, 4);
        int l1 = region.addLayer(30, 6, 3);

        region.bindInput("pixels", List.of(l0));
        region.connectLayers(l0, l1, 0.10, false);
        region.connectLayers(l1, l0, 0.01, true);

        Random rng = new Random();
        for (int step = 1; step <= 2000; step++) {
            Region.RegionMetrics m = region.tick("pixels", rng.nextDouble());
            if (step % 200 == 0) {
                System.out.printf("[step %d] delivered=%d slots=%d syn=%d%n",
                        step, m.deliveredEvents(), m.totalSlots(), m.totalSynapses());
            }
        }
        Region.PruneSummary p = region.prune();
        System.out.println("Prune summary: " + p);
    }
}
