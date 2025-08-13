package ai.nektron.grownet;

import java.util.List;
import java.util.Map;
import java.util.Random;

public class ImageIODemo {
    public static void main(String[] args) {
        final int h = 28, w = 28;
        Region region = new Region("image_io");

        int lIn     = region.addInputLayer2D(h, w, 1.0, 0.01);
        int lHidden = region.addLayer(64, 8, 4);
        int lOut    = region.addOutputLayer2D(h, w, 0.20);

        region.bindInput("pixels", List.of(lIn));
        region.connectLayers(lIn, lHidden, 0.05, false);
        region.connectLayers(lHidden, lOut, 0.12, false);

        Random rnd = new Random(42);
        for (int step = 0; step < 20; step++) {
            // Generate a sparse random image (or swap to a moving dot if you prefer determinism)
            double[][] frame = new double[h][w];
            for (int y = 0; y < h; y++) {
                for (int x = 0; x < w; x++) {
                    frame[y][x] = (rnd.nextDouble() > 0.95) ? 1.0 : 0.0;
                }
            }

            Map<String, Double> m = region.tickImage("pixels", frame);

            if ((step + 1) % 5 == 0) {
                OutputLayer2D out = (OutputLayer2D) region.getLayers().get(lOut);
                double[][] img = out.getFrame();

                double sum = 0.0;
                int nonZero = 0;
                for (int y = 0; y < h; y++) {
                    for (int x = 0; x < w; x++) {
                        sum += img[y][x];
                        if (img[y][x] > 0.05) nonZero++;
                    }
                }
                double mean = sum / (h * w);
                System.out.printf("[%02d] delivered=%d out_mean=%.3f out_nonzero=%d%n",
                        step + 1,
                        m.get("delivered_events").intValue(),
                        mean,
                        nonZero
                );
            }
        }
    }
}
