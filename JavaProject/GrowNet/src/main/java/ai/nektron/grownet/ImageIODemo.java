package ai.nektron.grownet;

import java.util.List;
import java.util.Random;

public class ImageIODemo {
    public static void main(String[] args) {
        final int height = 28, width = 28;
        Region region = new Region("image_io");

        int inputLayerIndex   = region.addInputLayer2D(height, width, 1.0, 0.01);
        int hiddenLayerIndex  = region.addLayer(64, 8, 4);
        int outputLayerIndex  = region.addOutputLayer2D(height, width, 0.20);

        region.bindInput("pixels", List.of(inputLayerIndex));
        region.connectLayers(inputLayerIndex, hiddenLayerIndex, 0.05, false);
        region.connectLayers(hiddenLayerIndex, outputLayerIndex, 0.12, false);

        Random rnd = new Random(42);
        for (int step = 0; step < 20; step++) {
            // sparse random image
            double[][] frame = new double[height][width];
            for (int y = 0; y < height; y++) {
                for (int x = 0; x < width; x++) {
                    frame[y][x] = (rnd.nextDouble() > 0.95) ? 1.0 : 0.0;
                }
            }

            Region.Metrics m = region.tickImage("pixels", frame);

            if ((step + 1) % 5 == 0) {
                OutputLayer2D out = (OutputLayer2D) region.getLayers().get(outputLayerIndex);
                double[][] img = out.getFrame();

                double sum = 0.0;
                int nonZero = 0;
                for (int y = 0; y < height; y++) {
                    for (int x = 0; x < width; x++) {
                        sum += img[y][x];
                        if (img[y][x] > 0.05) nonZero++;
                    }
                }
                double mean = sum / (height * width);
                System.out.printf("[%02d] delivered=%d out_mean=%.3f out_nonzero=%d%n",
                        step + 1,
                        m.deliveredEvents,
                        mean,
                        nonZero
                );
            }
        }
    }
}
