package ai.nektron.grownet;

import java.util.List;

/** Shape-aware sensory layer (e.g., grayscale image). */
public class InputLayer2D extends Layer {
    private final int height;
    private final int width;

    public InputLayer2D(int height, int width, double gain, double epsilonFire) {
        super(0, 0, 0);
        this.height = height;
        this.width  = width;
        List<Neuron> list = getNeurons();
        for (int y = 0; y < height; y++) {
            for (int x = 0; x < width; x++) {
                list.add(new InputNeuron("IN[" + y + "," + x + "]", gain, epsilonFire));
            }
        }
    }

    public int index(int y, int x) { return y * width + x; }

    public void forwardImage(double[][] image) {
        for (int y = 0; y < height; y++) {
            for (int x = 0; x < width; x++) {
                int idx = index(y, x);
                InputNeuron n = (InputNeuron) getNeurons().get(idx);
                n.onSensorValue(image[y][x], getBus().getModulationFactor(), getBus().getInhibitionFactor());
            }
        }
    }

    @Override
    public void propagateFrom(int sourceIndex, double value) {
        // entry layer: no intra-layer routing
    }
}
