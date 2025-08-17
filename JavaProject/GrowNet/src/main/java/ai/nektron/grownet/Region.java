package ai.nektron.grownet;

import ai.nektron.grownet.metrics.RegionMetrics;

import java.util.*;

/**
 * Region: groups layers, owns simple wiring helpers and tick/prune orchestration.
 * API matches the demos (addLayer, connectLayers, bindInput, tick, prune),
 * and keeps parity with the C++/docs counterparts.
 */
public final class Region {

    public static final class PruneSummary {
        public int prunedSynapses = 0;
        public int prunedEdges    = 0;    // reserved for future inter-layer tract pruning
    }

    // ------------------------------ fields -------------------------------
    private final String name;
    private final List<Layer> layers = new ArrayList<>();
    private final Map<String, List<Integer>> inputPorts  = new HashMap<>();
    private final Map<String, List<Integer>> outputPorts = new HashMap<>();
    private final RegionBus bus = new RegionBus();   // reserved for future tract batching
    private final Random rng = new Random(1234);

    // --------------------------- construction ----------------------------
    public Region(String name) { this.name = name; }

    /** Create a mixed layer. Returns the index of the new layer. */
    public int addLayer(int excitatoryCount, int inhibitoryCount, int modulatoryCount) {
        Layer layer = new Layer(excitatoryCount, inhibitoryCount, modulatoryCount);
        layers.add(layer);
        return layers.size() - 1;
    }

    /** Create a shape-aware input layer (e.g., grayscale image). */
    public int addInputLayer2D(int height, int width, double gain, double epsilonFire) {
        InputLayer2D in = new InputLayer2D(height, width, gain, epsilonFire);
        layers.add(in);
        return layers.size() - 1;
    }

    /** Create a shape-aware output layer (e.g., image writer). */
    public int addOutputLayer2D(int height, int width, double smoothing) {
        OutputLayer2D out = new OutputLayer2D(height, width, smoothing);
        layers.add(out);
        return layers.size() - 1;
    }

    // ------------------------------ wiring -------------------------------
    /**
     * Randomly connect every neuron in source layer to neurons in destination
     * layer with probability {@code probability}. If {@code feedback} is true,
     * mark created synapses as feedback edges (your Neuron.connect handles this flag).
     * @return number of edges created
     */
    public int connectLayers(int sourceIndex, int destIndex, double probability, boolean feedback) {
        if (sourceIndex < 0 || sourceIndex >= layers.size())
            throw new IndexOutOfBoundsException("sourceIndex out of range");
        if (destIndex < 0 || destIndex >= layers.size())
            throw new IndexOutOfBoundsException("destIndex out of range");
        if (probability < 0.0) probability = 0.0;
        if (probability > 1.0) probability = 1.0;

        Layer src = layers.get(sourceIndex);
        Layer dst = layers.get(destIndex);

        int edges = 0;
        for (Neuron neuronA : src.getNeurons()) {
            for (Neuron neuronB : dst.getNeurons()) {
                if (neuronA == neuronB) continue;                  // defensive; layers differ anyway
                if (rng.nextDouble() < probability) {
                    neuronA.connect(neuronB, feedback);
                    edges++;
                }
            }
        }
        return edges;
    }

    /** Convenient overload; defaults to feedforward (no feedback flag). */
    public int connectLayers(int sourceIndex, int destIndex, double probability) {
        return connectLayers(sourceIndex, destIndex, probability, false);
    }

    /** Bind an external named input port to one or more entry layers. */
    public void bindInput(String port, List<Integer> layerIndices) {
        inputPorts.put(port, new ArrayList<>(layerIndices));
    }

    /** (Reserved) output binding — kept for symmetry/future dashboards. */
    public void bindOutput(String port, List<Integer> layerIndices) {
        outputPorts.put(port, new ArrayList<>(layerIndices));
    }

    // -------------------------------- tick -------------------------------
    /**
     * Drive all entry layers bound to {@code port} with {@code value} (single scalar per tick).
     * Returns lightweight metrics. (deliveredEvents remains a best‑effort placeholder unless
     * your Layer/Neuron tracks it explicitly.)
     */
    public RegionMetrics tick(String port, double value) {
        RegionMetrics regionMetrics = new RegionMetrics();

        List<Integer> entry = inputPorts.get(port);
        if (entry != null) {
            for (int idx : entry) {
                layers.get(idx).forward(value);
                regionMetrics.incDeliveredEvents(); // best‑effort placeholder
            }
        }

        // End‑of‑tick housekeeping for each layer (decay bus, etc.)
        for (Layer layer : layers) {
            layer.endTick();
        }

        // Aggregate simple counts for visibility
        for (Layer layer : layers) {
            for (Neuron neuron : layer.getNeurons()) {
                regionMetrics.addSlots(neuron.getSlots().size());
                regionMetrics.addSynapses(neuron.getOutgoing().size());
            }
        }
        return regionMetrics;
    }

    /**
     * Drive this region with a 2D image (values in [0, 1] or any float range).
     * Follows the same onInput/onOutput contract as scalar ticks.
     */
    public RegionMetrics tickImage(String port, double[][] frame) {
        RegionMetrics regionMetrics = new RegionMetrics();

        List<Integer> entry = inputPorts.get(port);
        if (entry != null) {
            for (int idx : entry) {
                Layer layer = layers.get(idx);
                if (layer instanceof InputLayer2D) {
                    ((InputLayer2D) layer).forwardImage(frame);
                    regionMetrics.incDeliveredEvents();   // per entry layer
                }
            }
        }

        // End‑of‑tick housekeeping
        for (Layer layer : layers) {
            layer.endTick();
        }

        // Aggregates
        for (Layer layer : layers) {
            for (Neuron neuron : layer.getNeurons()) {
                regionMetrics.addSlots(neuron.getSlots().size());
                regionMetrics.addSynapses(neuron.getOutgoing().size());
            }
        }
        return regionMetrics;
    }

    // ----------------------------- maintenance ---------------------------
    /**
     * Prune weak/stale synapses (and optionally tract‑level links in the future).
     * Java version keeps a two‑argument signature for simplicity.
     */
    public PruneSummary prune(long synapseStaleWindow, double synapseMinStrength) {
        PruneSummary ps = new PruneSummary();
        for (Layer layer : layers) {
            for (Neuron neuron : layer.getNeurons()) {
                ps.prunedSynapses += neuron.pruneSynapses(synapseStaleWindow, synapseMinStrength);
            }
        }
        // ps.prunedEdges stays zero until you track inter‑layer tracts explicitly
        return ps;
    }

    // ------------------------------ accessors ----------------------------
    public String getName() { return name; }
    public List<Layer> getLayers() { return layers; }
    /** Back‑compat alias; prefer {@link #getLayers()}. */
    public List<Layer> layers() { return layers; }
    public RegionBus getBus() { return bus; }
}
