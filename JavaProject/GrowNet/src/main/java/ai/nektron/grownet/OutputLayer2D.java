package ai.nektron.grownet;

import java.util.List;

/**
 * Shape-aware output layer (e.g., image writer) using unified onInput/onOutput.
 */
public class OutputLayer2D extends Layer {

    private final int height;
    private final int width;
    private final double[][] frame;

    public OutputLayer2D(int height, int width, double smoothing) {
        // Base Layer constructs the lateral bus; no E/I/M neurons are created here.
        super(0, 0, 0);

        this.height = height;
        this.width  = width;
        this.frame  = new double[height][width];

        // Create one OutputNeuron per pixel.
        List<Neuron> neurons = getNeurons();
        for (int y = 0; y < height; ++y) {
            for (int x = 0; x < width; ++x) {

                neurons.add(new OutputNeuron("OUT[" + y + "," + x + "]",
                        getBus(),
                        SlotConfig.singleSlot()));

                // If your OutputNeuron ctor instead takes (id, bus, smoothing),
                // use this alternative:
                // neurons.add(new OutputNeuron("OUT[" + y + "," + x + "]", getBus(), smoothing));
            }
        }
    }

    /** Row-major index helper. */
    public int index(int y, int x) { return y * width + x; }

    /** Route a scalar into the output neuron with the given index. */

    public void propagateFrom(int sourceIndex, double value) {
        if (sourceIndex < 0 || sourceIndex >= getNeurons().size()) return;

        OutputNeuron outputNeuron = (OutputNeuron) getNeurons().get(sourceIndex);

        // Unified contract: bus factors are read inside the neuron.
        boolean fired = outputNeuron.onInput(value);
        if (fired) {
            outputNeuron.onOutput(value);
        }
    }

    /** End-of-tick housekeeping + snapshot the last output frame. */
    @Override
    public void endTick() {
        // Allow the layer bus to decay toward neutral this tick.
        super.endTick();

        for (int index = 0; index < getNeurons().size(); ++index) {
            OutputNeuron outputNeuron = (OutputNeuron) getNeurons().get(index);
            outputNeuron.endTick();

            int y = index / width;
            int x = index % width;
            frame[y][x] = outputNeuron.getOutputValue();
        }
    }

    /** Convenience for dashboards: last output image. */
    public double[][] getFrame() {
        return frame;
    }
}
