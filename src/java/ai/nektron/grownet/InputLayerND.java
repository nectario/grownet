
package ai.nektron.grownet;

import java.util.Arrays;
import java.util.List;

/**
 * Shape-agnostic sensory Layer that owns one InputNeuron per element of an N-D tensor.
 * Data is delivered as a flat row-major array alongside an explicit shape.
 */
public class InputLayerND extends Layer {

    private final int[] shape;     // immutable copy
    private final int   size;      // product(shape)

    /**
     * Manage our own input neurons; base layer creates none.
     * @param shape row-major dimensions (rank >= 1, each > 0)
     * @param gain scales each value before thresholding
     * @param epsilonFire minimal amplitude to be considered active
     */
    public InputLayerND(int[] shape, double gain, double epsilonFire) {
        super(0, 0, 0);  // no E/I/M neurons; we manage InputNeurons explicitly
        if (shape == null || shape.length == 0)
            throw new IllegalArgumentException("shape must be rank >= 1");
        int prod = 1;
        for (int d : shape) {
            if (d <= 0) throw new IllegalArgumentException("shape dims must be > 0");
            long tmp = (long) prod * (long) d;
            if (tmp > Integer.MAX_VALUE) throw new IllegalArgumentException("shape too large");
            prod *= d;
        }
        this.shape = Arrays.copyOf(shape, shape.length);
        this.size  = prod;

        // Create one InputNeuron per element
        List<Neuron> list = getNeurons();
        for (int i = 0; i < size; ++i) {
            InputNeuron n = new InputNeuron("IN[" + i + "]", getBus(), gain, epsilonFire);
            n.owner = this;
            list.add(n);
        }
    }

    /** Row-major size */
    public int size() { return size; }

    /** True iff the provided shape matches the bound shape exactly. */
    public boolean hasShape(int[] another) {
        return Arrays.equals(this.shape, another);
    }

    /** Return a defensive copy of the bound shape. */
    public int[] getShape() { return Arrays.copyOf(shape, shape.length); }

    /**
     * Drive this input Layer with flat row-major data and explicit shape.
     * Validates shape/length and runs unified onInput/onOutput contract.
     */
    public void forwardND(double[] flat, int[] shape) {
        if (!hasShape(shape))
            throw new IllegalArgumentException("shape mismatch with bound InputLayerND");
        if (flat == null || flat.length != size)
            throw new IllegalArgumentException("flat length " + (flat == null ? -1 : flat.length) + " != expected " + size);

        List<Neuron> list = getNeurons();
        for (int i = 0; i < size; ++i) {
            InputNeuron n = (InputNeuron) list.get(i);
            double value = flat[i];
            boolean fired = n.onInput(value);
            if (fired) n.onOutput(value);
        }
    }

    /** Entry layers do not perform intra-layer routing. */
    public void propagateFrom(int sourceIndex, double value) {
        // no-op for InputLayerND
    }
}
