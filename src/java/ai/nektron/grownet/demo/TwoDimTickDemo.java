package ai.nektron.grownet.demo;

import ai.nektron.grownet.Region;
import ai.nektron.grownet.metrics.RegionMetrics;
import java.util.Arrays;

public final class TwoDimTickDemo {
    public static void main(String[] args) {
        int height = 8, width = 8;
        Region region = new Region("two-d-tick-demo");
        region.setEnableSpatialMetrics(true);

        int inputIndex  = region.addInputLayer2D(height, width, 1.0, 0.01);
        int outputIndex = region.addOutputLayer2D(height, width, 0.0);

        int uniqueSources = region.connectLayersWindowed(inputIndex, outputIndex, 3, 3, 1, 1, "same", false);
        System.out.println("unique_sources=" + uniqueSources);

        region.bindInput2D("pixels", height, width, 1.0, 0.01, Arrays.asList(inputIndex));

        double[][] frame = new double[height][width];
        frame[3][4] = 1.0;
        RegionMetrics m1 = region.tick2D("pixels", frame);
        System.out.printf("tick#1 delivered=%d slots=%d synapses=%d active=%d centroid=(%.3f,%.3f) bbox=(%d,%d,%d,%d)%n",
                m1.getDeliveredEvents(), m1.getTotalSlots(), m1.getTotalSynapses(),
                m1.getActivePixels(), m1.getCentroidRow(), m1.getCentroidCol(),
                m1.getBboxRowMin(), m1.getBboxRowMax(), m1.getBboxColMin(), m1.getBboxColMax());

        frame[3][4] = 0.0; frame[5][6] = 1.0;
        RegionMetrics m2 = region.tick2D("pixels", frame);
        System.out.printf("tick#2 delivered=%d slots=%d synapses=%d active=%d centroid=(%.3f,%.3f) bbox=(%d,%d,%d,%d)%n",
                m2.getDeliveredEvents(), m2.getTotalSlots(), m2.getTotalSynapses(),
                m2.getActivePixels(), m2.getCentroidRow(), m2.getCentroidCol(),
                m2.getBboxRowMin(), m2.getBboxRowMax(), m2.getBboxColMin(), m2.getBboxColMax());
    }
}

