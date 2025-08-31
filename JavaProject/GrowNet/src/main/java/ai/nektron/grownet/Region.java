package ai.nektron.grownet;

import ai.nektron.grownet.metrics.RegionMetrics;
import ai.nektron.grownet.growth.GrowthPolicy;
import ai.nektron.grownet.growth.GrowthEngine;

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
    
    // Edge layers per port (auto-created on bind)
    private final Map<String, Integer> inputEdges = new HashMap<>();
    private final Map<String, Integer> outputEdges = new HashMap<>();
    private final RegionBus bus = new RegionBus();   // reserved for future tract batching
    private final Random rng = new Random(1234);

    // [GROWNET:ANCHOR::AFTER_METRICS]
    private GrowthPolicy growthPolicy = null;   // optional, controls best‑effort growth

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


/** Create a shape-aware N-D input layer defined by shape[] (row-major). */
public int addInputLayerND(int[] shape, double gain, double epsilonFire) {
    InputLayerND in = new InputLayerND(shape, gain, epsilonFire);
    layers.add(in);
    return layers.size() - 1;
}



    /** Create a shape-aware output layer (e.g., image writer). */
    public int addOutputLayer2D(int height, int width, double smoothing) {
        OutputLayer2D out = new OutputLayer2D(height, width, smoothing);
        layers.add(out);
        return layers.size() - 1;
    }

    
    // ------------------------------ edge helpers ---------------------------
    /** Ensure there is an Input edge layer for this port; create lazily if missing. */
    private int ensureInputEdge(String port) {
        Integer idx = inputEdges.get(port);
        if (idx != null) return idx;
        // Minimal scalar input edge: a 1-neuron layer that forwards into the graph.
        int edge = addLayer(1, 0, 0);
        inputEdges.put(port, edge);
        return edge;
    }

    /** Ensure there is an Output edge layer for this port; create lazily if missing. */
    private int ensureOutputEdge(String port) {
        Integer idx = outputEdges.get(port);
        if (idx != null) return idx;
        // Minimal scalar output edge: a 1-neuron layer acting as a sink (placeholder).
        int edge = addLayer(1, 0, 0);
        outputEdges.put(port, edge);
        return edge;
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

    /** Bind scalar input: create/reuse InputEdge(port) and wire it → target layers (p=1.0). */
    public void bindInput(String port, List<Integer> layerIndices) {
        Objects.requireNonNull(port, "port");
        Objects.requireNonNull(layerIndices, "layerIndices");
        inputPorts.put(port, List.copyOf(layerIndices)); // for introspection only

        int edge = ensureInputEdge(port);
        for (int li : layerIndices) {
            connectLayers(edge, li, /*probability=*/1.0, /*feedback=*/false);
        }
    }

    /** Bind scalar output: wire target layers → OutputEdge(port) (p=1.0). */
    public void bindOutput(String port, List<Integer> layerIndices) {
        Objects.requireNonNull(port, "port");
        Objects.requireNonNull(layerIndices, "layerIndices");
        outputPorts.put(port, List.copyOf(layerIndices));

        int edge = ensureOutputEdge(port);
        for (int li : layerIndices) {
            connectLayers(li, edge, /*probability=*/1.0, /*feedback=*/false);
        }
    }

    /** Bind a 2D input edge; creates InputLayer2D edge if absent or wrong type, then wires it → targets. */
    public void bindInput2D(String port, int height, int width, double gain, double epsilonFire, List<Integer> layerIndices) {

        Integer idx = inputEdges.get(port);
        if (idx != null && !(layers.get(idx) instanceof InputLayer2D)) {
            throw new IllegalStateException(
                    "Port '" + port + "' already bound as scalar. Use a different port or unbind first.");
        }

        Objects.requireNonNull(port, "port");
        Objects.requireNonNull(layerIndices, "layerIndices");

        idx = inputEdges.get(port);
        boolean needNew2D = true;
        if (idx != null) {
            Layer maybe = layers.get(idx);
            needNew2D = !(maybe instanceof InputLayer2D);
        }
        if (idx == null || needNew2D) {
            int edgeIndex = addInputLayer2D(height, width, gain, epsilonFire);
            inputEdges.put(port, edgeIndex);
            idx = edgeIndex;
        }
        inputPorts.put(port, List.copyOf(layerIndices));

        for (int li : layerIndices) {
            connectLayers(idx, li, /*probability=*/1.0, /*feedback=*/false);
        }
    }


    /** Bind an N-D input edge; creates InputLayerND if absent or wrong type/shape, then wires it → targets. */
    public void bindInputND(String port, int[] shape, double gain, double epsilonFire, List<Integer> layerIndices) {
        Objects.requireNonNull(port, "port");
        Objects.requireNonNull(shape, "shape");
        Objects.requireNonNull(layerIndices, "layerIndices");
    
        Integer idx = inputEdges.get(port);
        boolean needNew = true;
        if (idx != null) {
            Layer maybe = layers.get(idx);
            if (maybe instanceof InputLayerND) {
                InputLayerND nd = (InputLayerND) maybe;
                needNew = !nd.hasShape(shape);
            }
        }
        if (idx == null || needNew) {
            int edgeIndex = addInputLayerND(shape, gain, epsilonFire);
            inputEdges.put(port, edgeIndex);
            idx = edgeIndex;
        }
        inputPorts.put(port, List.copyOf(layerIndices)); // introspection only
        for (int li : layerIndices) {
            connectLayers(idx, li, /*probability=*/1.0, /*feedback=*/false);
        }
    }



    
    // ------------------------------ pulses (region-wide) -------------------
    /** Temporarily raise inhibition for the next tick (applies to all layer buses). */
    public void pulseInhibition(double factor) {
        bus.setInhibitionFactor(factor);
        for (Layer layer : layers) {
            layer.getBus().setInhibitionFactor(factor);
        }
    }

    /** Temporarily scale modulation for the next tick (applies to all layer buses). */
    public void pulseModulation(double factor) {
        bus.setModulationFactor(factor);
        for (Layer layer : layers) {
            layer.getBus().setModulationFactor(factor);
        }
    }

    // -------------------------------- tick -------------------------------
    /**
     * Drive all entry layers bound to {@code port} with {@code value} (single scalar per tick).
     * Returns lightweight metrics. (deliveredEvents remains a best‑effort placeholder unless
     * your Layer/Neuron tracks it explicitly.)
     */
    /** Scalar tick: port must be bound to a scalar InputEdge (via bindInput). */
    public RegionMetrics tick(String port, double value) {

        RegionMetrics regionMetrics = new RegionMetrics();

        Integer edgeIdx = inputEdges.get(port);
        if (edgeIdx == null) {
            throw new IllegalArgumentException("No InputEdge for port '" + port + "'. Call bindInput(...) first.");
        }

        layers.get(edgeIdx).forward(value);
        regionMetrics.incDeliveredEvents();

        // End-of-tick housekeeping
        for (Layer l : layers) l.endTick();
        bus.decay();

        // Structural metrics
        for (Layer l : layers) {
            for (Neuron neuron : l.getNeurons()) {
                regionMetrics.addSlots(neuron.getSlots().size());
                regionMetrics.addSynapses(neuron.getOutgoing().size());
            }
        }
        // Best‑effort growth hook
        try {
            if (growthPolicy != null) {
                GrowthEngine.maybeGrowNeurons(this, growthPolicy);
            }
        } catch (Throwable ignored) { }
        return regionMetrics;
    }


    /**
     * Drive this region with a 2D image (values in [0, 1] or any float range).
     * Follows the same onInput/onOutput contract as scalar ticks.
     */
    /** 2D tick (image-agnostic name). Port must be bound to a 2D InputEdge (InputLayer2D). */

    /** N-D tick: deliver a flat row-major array with explicit shape to an InputLayerND edge. */
    public RegionMetrics tickND(String port, double[] flat, int[] shape) {
        RegionMetrics metrics = new RegionMetrics();

        Integer edge = inputEdges.get(port);
        if (edge == null)
            throw new IllegalArgumentException("No InputEdge for port '" + port + "'. Call bindInputND(...) first.");

        Layer layer = layers.get(edge);
        if (!(layer instanceof InputLayerND))
            throw new IllegalArgumentException("InputEdge for '" + port + "' is not ND (expected InputLayerND).");

        ((InputLayerND) layer).forwardND(flat, shape);
        metrics.incDeliveredEvents();

        for (Layer l : layers) l.endTick();
        bus.decay();

        for (Layer l : layers) {
            for (Neuron neuron : l.getNeurons()) {
                metrics.addSlots(neuron.getSlots().size());
                metrics.addSynapses(neuron.getOutgoing().size());
            }
        }
        return metrics;
    }

    public RegionMetrics tick2D(String port, double[][] frame) {
        RegionMetrics metrics = new RegionMetrics();

        Integer edge = inputEdges.get(port);
        if (edge == null)
            throw new IllegalArgumentException("No InputEdge for port '" + port + "'. Call bindInput2D(...) first.");

        Layer layer = layers.get(edge);
        if (!(layer instanceof InputLayer2D))
            throw new IllegalArgumentException("InputEdge for '" + port + "' is not 2D (expected InputLayer2D).");

        ((InputLayer2D) layer).forwardImage(frame);
        metrics.incDeliveredEvents();

        // End-of-tick housekeeping
        for (Layer l : layers) l.endTick();
        bus.decay();

        // Aggregate structure metrics
        for (Layer l : layers) {
            for (Neuron neuron : l.getNeurons()) {
                metrics.addSlots(neuron.getSlots().size());
                metrics.addSynapses(neuron.getOutgoing().size());
            }
        }
        return metrics;
    }

    public RegionMetrics tickImage(String port, double[][] frame) {
        return tick2D(port, frame);
    }


    // ----------------------------- maintenance ---------------------------
    /**
     * Prune weak/stale synapses (and optionally tract‑level links in the future).
     * Java version keeps a two‑argument signature for simplicity.
     */
    public PruneSummary prune(long synapseStaleWindow, double synapseMinStrength) {
        PruneSummary pruneSummary = new PruneSummary();
        for (Layer layer : layers) {
            for (Neuron neuron : layer.getNeurons()) {
                pruneSummary.prunedSynapses += neuron.pruneSynapses(synapseStaleWindow, synapseMinStrength);
            }
        }
        // pruneSummary.prunedEdges stays zero until you track inter‑layer tracts explicitly
        return pruneSummary;
    }

    // ------------------------------ accessors ----------------------------
    public String getName() { return name; }
    public List<Layer> getLayers() { return layers; }
    /** Back‑compat alias; prefer {@link #getLayers()}. */
    public List<Layer> layers() { return layers; }
    public RegionBus getBus() { return bus; }

    // ------------------------------ growth policy ---------------------------
    public GrowthPolicy getGrowthPolicy() { return growthPolicy; }
    public Region setGrowthPolicy(GrowthPolicy gp) { this.growthPolicy = gp; return this; }
}
