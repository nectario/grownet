package ai.nektron.grownet.tests;

import ai.nektron.grownet.Region;
import ai.nektron.grownet.metrics.RegionMetrics;
import java.util.List;

public class RegionTickTests {
    private static void check(boolean cond, String msg) {
        if (!cond) throw new RuntimeException("Test failed: " + msg);
    }

    private static void testSingleTickNoTracts() {
        Region region = new Region("t");
        int inputLayer = region.addLayer(1, 0, 0);
        region.bindInput("x", List.of(inputLayer));

        RegionMetrics metrics = region.tick("x", 0.42);
        System.out.println("[JAVA] singleTickNoTracts -> " + metrics);
        check(metrics.getDeliveredEvents() == 1, "deliveredEvents should be 1");
        check(metrics.getTotalSlots() >= 1, "totalSlots >= 1");
        check(metrics.getTotalSynapses() >= 0, "totalSynapses >= 0");
    }

    private static void testConnectLayersFullMesh() {
        Region region = new Region("t");
        int src = region.addLayer(2, 0, 0);
        int dst = region.addLayer(3, 0, 0);
        int edges = region.connectLayers(src, dst, 1.0, false);
        System.out.println("[JAVA] connectLayersFullMesh -> edges=" + edges);
        check(edges == 2*3, "edge count must equal 2*3 for full mesh");
    }

    private static void testImageInputEventCount() {
        Region region = new Region("t");
        int inputLayerId = region.addInputLayer2D(2, 2, 1.0, 0.01);
        region.bindInput("pixels", List.of(inputLayerId));
        double[][] frame = new double[][] { {0.0, 1.0}, {0.0, 0.0} };
        RegionMetrics metrics = region.tickImage("pixels", frame);
        System.out.println("[JAVA] imageInputEventCount -> " + metrics);
        check(metrics.getDeliveredEvents() == 1, "image tick should count as 1 event per bound entry layer");
    }

    public static void main(String[] args) {
        testSingleTickNoTracts();
        testConnectLayersFullMesh();
        testImageInputEventCount();
        System.out.println("[JAVA] All RegionTickTests passed.");
    }
}
