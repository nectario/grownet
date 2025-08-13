package ai.nektron.grownet;

import java.util.*;

/**
 * Region = a small group of layers plus inter-layer tracts,
 * scheduled with a two-phase tick:
 *   Phase A: inject external input to entry layers (intra-layer propagation).
 *   Phase B: flush inter-layer tracts once; finalize outputs; decay buses.
 */
public final class Region {

    private static final double DEFAULT_INPUT_GAIN = 1.0;
    private static final double DEFAULT_EPSILON_FIRE = 0.01;
    private static final double DEFAULT_OUTPUT_SMOOTHING = 0.20;

    private final String name;
    private final List<Layer> layers = new ArrayList<>();
    private final List<Tract> tracts = new ArrayList<>();
    private final Map<String, List<Integer>> inputPorts = new HashMap<>();

    public Region(String name) {
        this.name = name;
    }

    // ----- Layer factories (Java bindings per v2 API) -----

    /** Hidden mixed-type layer. */
    public int addLayer(int excitatoryCount, int inhibitoryCount, int modulatoryCount) {
        Layer layer = new Layer(excitatoryCount, inhibitoryCount, modulatoryCount);
        layers.add(layer);
        return layers.size() - 1;
    }

    /** 2D input layer (shape-aware). */
    public int addInputLayer2D(int height, int width, double gain, double epsilonFire) {
        InputLayer2D layer = new InputLayer2D(height, width, gain, epsilonFire);
        layers.add(layer);
        return layers.size() - 1;
    }

    /** Convenience overload using defaults. */
    public int addInputLayer2D(int height, int width) {
        return addInputLayer2D(height, width, DEFAULT_INPUT_GAIN, DEFAULT_EPSILON_FIRE);
    }

    /** 2D output layer (frame buffer). */
    public int addOutputLayer2D(int height, int width, double smoothing) {
        OutputLayer2D layer = new OutputLayer2D(height, width, smoothing);
        layers.add(layer);
        return layers.size() - 1;
    }

    /** Convenience overload using default smoothing. */
    public int addOutputLayer2D(int height, int width) {
        return addOutputLayer2D(height, width, DEFAULT_OUTPUT_SMOOTHING);
    }

    // ----- Wiring & binding -----

    /** Bind a named input port to one or more entry layers (usually InputLayer2D). */
    public void bindInput(String port, List<Integer> layerIndexes) {
        inputPorts.put(port, new ArrayList<>(layerIndexes));
    }

    /** Connect two layers via a new tract; random dense wiring with given probability. */
    public Tract connectLayers(int sourceIndex, int destIndex, double probability, boolean feedback) {
        Layer source = layers.get(sourceIndex);
        Layer dest = layers.get(destIndex);
        Tract tract = new Tract(source, dest, feedback);
        tract.wireDenseRandom(probability);
        tracts.add(tract);
        return tract;
    }

    // ----- Tick (image) -----

    /**
     * Run one image tick:
     * Phase A: deliver image to bound input layers and run intra-layer propagation.
     * Phase B: flush tracts once, finalize output layers, decay layer buses.
     * Returns lightweight metrics.
     */
    public Map<String, Double> tickImage(String port, double[][] image) {
        // Phase A — inject to all layers bound to this port
        List<Integer> entries = inputPorts.getOrDefault(port, Collections.emptyList());
        for (int idx : entries) {
            Layer layer = layers.get(idx);
            if (layer instanceof InputLayer2D input) {
                input.forwardImage(image);
            } else {
                // If a non-image layer is accidentally bound, ignore safely.
            }
        }

        // Phase B — flush inter-layer tracts exactly once
        int delivered = 0;
        for (Tract t : tracts) {
            delivered += t.flush();
        }

        // Finalize outputs (EMA to frame)
        for (Layer layer : layers) {
            if (layer instanceof OutputLayer2D out) {
                out.endTick();
            }
        }

        // Decay layer buses
        for (Layer layer : layers) {
            layer.getBus().decay();
        }

        // Metrics (simple, cheap)
        int totalSlots = 0;
        int totalSynapses = 0;
        for (Layer layer : layers) {
            totalSlots += layer.countSlots();
            totalSynapses += layer.countSynapses();
        }

        Map<String, Double> m = new LinkedHashMap<>();
        m.put("delivered_events", (double) delivered);
        m.put("total_slots", (double) totalSlots);
        m.put("total_synapses", (double) totalSynapses);
        return m;
    }

    // ----- Accessors -----

    public String getName() {
        return name;
    }

    /** Exposed so demos can read frames from the output layer. */
    public List<Layer> getLayers() {
        return layers;
    }
}
