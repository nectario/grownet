package ai.nektron.grownet.demo;

import ai.nektron.grownet.Region;
import ai.nektron.grownet.preset.TopographicConfig;
import ai.nektron.grownet.preset.TopographicWiring;

public final class TopographicDemo {
    public static void main(String[] args) {
        Region region = new Region("TopographicDemo");
        int src = region.addInputLayer2D(16, 16, 1.0, 0.01);
        int dst = region.addOutputLayer2D(16, 16, 0.0);

        TopographicConfig cfg = new TopographicConfig()
                .setKernel(7, 7)
                .setStride(1, 1)
                .setPadding("same")
                .setWeightMode("gaussian")
                .setSigmaCenter(2.0)
                .setNormalizeIncoming(true);

        int unique = TopographicWiring.connectLayersTopographic(region, src, dst, cfg);
        double[] sums = TopographicWiring.incomingSums(region, dst);
        System.out.println("unique_sources=" + unique);
        int[][] centers = new int[][] { {0,0}, {8,8}, {15,15} };
        for (int[] rc : centers) {
            int idx = rc[0] * 16 + rc[1];
            double sum = (idx >= 0 && idx < sums.length ? sums[idx] : 0.0);
            System.out.printf("center=(%d,%d) sum=%.6f%n", rc[0], rc[1], sum);
        }
    }
}

