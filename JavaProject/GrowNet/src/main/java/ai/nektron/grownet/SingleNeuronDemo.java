package ai.nektron.grownet;

import ai.nektron.grownet.Region;
import ai.nektron.grownet.metrics.RegionMetrics;
import java.util.List;

public class SingleNeuronDemo {
    public static void main(String[] args) {
        Region region = new Region("dbg");
        int l0 = region.addLayer(1, 0, 0);
        region.bindInput("x", List.of(l0));

        // Single tick
        RegionMetrics m0 = region.tick("x", 0.42);
        System.out.printf("delivered=%d slots=%d synapses=%d%n",
                m0.getDeliveredEvents(), m0.getTotalSlots(), m0.getTotalSynapses());

        // Optional: add a second layer and a sure tract to watch propagation
        int l1 = region.addLayer(1, 0, 0);
        region.connectLayers(l0, l1, 1.0, false);
        RegionMetrics m1 = region.tick("x", 0.95);
        System.out.printf("delivered=%d slots=%d synapses=%d%n",
                m1.getDeliveredEvents(), m1.getTotalSlots(), m1.getTotalSynapses());
    }
}
