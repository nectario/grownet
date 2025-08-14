package ai.nektron.grownet;

import java.util.List;

/**
 * Shape‑aware sensory Layer (e.g., grayscale image) using unified onInput/onOutput.
 * This layer creates a single-slot InputNeuron for every pixel in a (height × width) grid.
 */
public class InputLayer2D extends Layer {

    private final int height;
    private final int width;

    /**
     * Manage our own input neurons; no E/I/M neurons are created by the base.
     * @param gain scales each pixel value before thresholding
     * @param epsilonFire tiny floor; values below this do not trigger a spike
     */
    public InputLayer2D(int height, int width, double gain, double epsilonFire) {
        super(/*excitatoryCount*/ 0, /*inhibitoryCount*/ 0, /*modulatoryCount*/ 0);
        this.height = height;
        this.width  = width;

        final List<Neuron> list = getNeurons();
        for (int y = 0; y < height; ++y) {
            for (int x = 0; x < width; ++x) {
                // InputNeuron is single‑slot; share the layer’s bus
                InputNeuron n = new InputNeuron(
                        "IN[" + y + "," + x + "]",
                        getBus(),
                        gain,
                        epsilonFire
                );
                list.add(n);
            }
        }
    }

    /** Row‑major index helper. */
    public int index(int y, int x) { return y * width + x; }

    /**
     * Drive this input Layer with a 2D image (values in [0, 1] or any float range).
     * Follows the same onInput/onOutput contract as other layers.
     */
    public void forwardImage(double[][] image) {
        // Optional: strict shape check
        if (image.length != height || (height > 0 && image[0].length != width)) {
            throw new IllegalArgumentException(
                    "image shape mismatch: expected " + height + "×" + width);
        }

        for (int y = 0; y < height; ++y) {
            for (int x = 0; x < width; ++x) {
                double value = image[y][x];
                InputNeuron n = (InputNeuron) getNeurons().get(index(y, x));
                boolean fired = n.onInput(value);     // unified API: single argument
                if (fired) n.onOutput(value);         // keeps the onOutput contract
            }
        }
    }

    /** Convenience for dashboards: snapshot the last output of each input neuron as an image. */
    public double[][] getFrame() {
        double[][] frame = new double[height][width];
        int idx = 0;
        for (int y = 0; y < height; ++y) {
            for (int x = 0; x < width; ++x) {
                frame[y][x] = ((InputNeuron) getNeurons().get(idx++)).getOutputValue();
            }
        }
        return frame;
    }

    /** Entry layers do not perform intra‑layer routing (no @Override unless Layer defines it). */
    public void propagateFrom(int sourceIndex, double value) {
        // no‑op by design for InputLayer2D
    }
}
