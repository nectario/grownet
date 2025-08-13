package ai.nektron.grownet;

import java.util.List;
import ai.nektron.grownet.Layer;

/** Shape-aware output layer (e.g., image writer) using unified onInput/onOutput. */
public class OutputLayer2D extends Layer {
    private final int height;
    private final int width;
    private final double[][] frame;

    public OutputLayer2D(int height, int width, double smoothing) {
        super(0, 0, 0);
        this.height = height;
        this.width  = width;
        this.frame  = new double[height][width];
        List<Neuron> list = getNeurons();
        for (int y = 0; y < height; y++) {
            for (int x = 0; x < width; x++) {
                list.add(new OutputNeuron("OUT[" + y + "," + x + "]", smoothing));
            }
        }
    }

    public int index(int y, int x) { return y * width + x; }

    @Override
    public void propagateFrom(int sourceIndex, double value) {
        if (sourceIndex < 0 || sourceIndex >= getNeurons().size()) return;
        OutputNeuron n = (OutputNeuron) getNeurons().get(sourceIndex);
        boolean fired = n.onInput(value, getBus().getModulationFactor(), getBus().getInhibitionFactor());
        if (fired) n.onOutput(value);
    }

    public void endTick() {
        for (int idx = 0; idx < getNeurons().size(); idx++) {
            OutputNeuron n = (OutputNeuron) getNeurons().get(idx);
            n.endTick();
            int y = idx / width, x = idx % width;
            frame[y][x] = n.getOutputValue();
        }
    }

    public double[][] getFrame() { return frame; }
}
