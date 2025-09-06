package ai.nektron.grownet;

import ai.nektron.grownet.metrics.RegionMetrics;

import java.util.List;
import java.util.Random;

public class ImageIODemo {
    public static void main(String[] args) {
        final int height = 28, width = 28;
        Region region = new Region("image_io");
        region.setEnableSpatialMetrics(true);

        int inputLayerIndex   = region.addInputLayer2D(height, width, 1.0, 0.01);
        int hiddenLayerIndex  = region.addLayer(64, 8, 4);
        int outputLayerIndex  = region.addOutputLayer2D(height, width, 0.20);

        // Bind a 2D input edge to the InputLayer2D edge; downstream layers are wired via connectLayers
        region.bindInput2D("pixels", height, width, 1.0, 0.01, List.of(inputLayerIndex));
        region.connectLayers(inputLayerIndex, hiddenLayerIndex, 0.05, false);
        region.connectLayers(hiddenLayerIndex, outputLayerIndex, 0.12, false);

        Random rnd = new Random(42);
        for (int step = 0; step < 20; step++) {
            // sparse random image
            double[][] frame = new double[height][width];
            for (int row = 0; row < height; row++) {
                for (int col = 0; col < width; col++) {
                    frame[row][col] = (rnd.nextDouble() > 0.95) ? 1.0 : 0.0;
                }
            }

            RegionMetrics metrics = region.tickImage("pixels", frame);

            if ((step + 1) % 5 == 0) {
                OutputLayer2D out = (OutputLayer2D) region.getLayers().get(outputLayerIndex);
                double[][] image = out.getFrame();

                double sum = 0.0;
                int nonZero = 0;
                for (int row = 0; row < height; row++) {
                    for (int col = 0; col < width; col++) {
                        sum += image[row][col];
                        if (image[row][col] > 0.05) nonZero++;
                    }
                }
                double mean = sum / (height * width);
                System.out.printf("[%02d] delivered=%d out_mean=%.3f out_nonzero=%d active=%d centroid=(%.3f,%.3f) bbox=(%d,%d,%d,%d)%n",
                        step + 1,
                        metrics.getDeliveredEvents(),
                        mean,
                        nonZero,
                        metrics.getActivePixels(),
                        metrics.getCentroidRow(), metrics.getCentroidCol(),
                        metrics.getBboxRowMin(), metrics.getBboxRowMax(), metrics.getBboxColMin(), metrics.getBboxColMax()
                );
            }
        }
    }
}
