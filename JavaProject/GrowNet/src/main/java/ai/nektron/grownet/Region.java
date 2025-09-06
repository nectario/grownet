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
    private final List<MeshRule> meshRules = new ArrayList<>();
    // Optional: track tracts if you decide to bridge via Tract; kept empty by default.
    private final List<Tract> tracts = new ArrayList<>();

    private static final class MeshRule {
        final int src, dst; final double prob; final boolean feedback;
        MeshRule(int s, int d, double p, boolean f) { src=s; dst=d; prob=p; feedback=f; }
    }

    // Spatial metrics toggle (opt-in)
    private boolean enableSpatialMetrics = false;

    // [GROWNET:ANCHOR::AFTER_METRICS]
    private GrowthPolicy growthPolicy = null;   // optional, controls best‑effort growth

    // --------------------------- construction ----------------------------
    public Region(String name) { this.name = name; }

    /** Create a mixed layer. Returns the index of the new layer. */
    public int addLayer(int excitatoryCount, int inhibitoryCount, int modulatoryCount) {
        Layer layer = new Layer(excitatoryCount, inhibitoryCount, modulatoryCount);
        try { layer.setRegion(this); } catch (Throwable ignored) {}
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
        meshRules.add(new MeshRule(sourceIndex, destIndex, probability, feedback));
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
        for (int layerIndex : layerIndices) {
            connectLayers(edge, layerIndex, /*probability=*/1.0, /*feedback=*/false);
        }
    }

    /** Bind scalar output: wire target layers → OutputEdge(port) (p=1.0). */
    public void bindOutput(String port, List<Integer> layerIndices) {
        Objects.requireNonNull(port, "port");
        Objects.requireNonNull(layerIndices, "layerIndices");
        outputPorts.put(port, List.copyOf(layerIndices));

        int edge = ensureOutputEdge(port);
        for (int layerIndex : layerIndices) {
            connectLayers(layerIndex, edge, /*probability=*/1.0, /*feedback=*/false);
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

        for (int layerIndex : layerIndices) {
            connectLayers(idx, layerIndex, /*probability=*/1.0, /*feedback=*/false);
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
        for (int layerIndex : layerIndices) {
            connectLayers(idx, layerIndex, /*probability=*/1.0, /*feedback=*/false);
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
    /** Drive a scalar into the edge bound to {@code port}; returns per-tick metrics. */
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
                GrowthEngine.maybeGrow(this, growthPolicy);
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
    /** Deliver a row-major flat tensor + shape into an InputLayerND edge. */
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
        // Best‑effort region growth (layers)
        try {
            if (growthPolicy != null) {
                GrowthEngine.maybeGrow(this, growthPolicy);
            }
        } catch (Throwable ignored) { }
        return metrics;
    }

    /** Drive a 2D frame into an InputLayer2D edge bound to {@code port}. */
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
        // Optional spatial metrics (env or flag)
        try {
            String env = System.getenv("GROWNET_ENABLE_SPATIAL_METRICS");
            boolean doSpatial = enableSpatialMetrics || "1".equals(env);
            if (doSpatial) {
                // Prefer furthest downstream OutputLayer2D frame; fallback to input if output is all zeros
                double[][] chosen = null;
                for (int i = layers.size() - 1; i >= 0; --i) {
                    Layer layer = layers.get(i);
                    if (layer instanceof OutputLayer2D) {
                        chosen = ((OutputLayer2D) layer).getFrame();
                        break;
                    }
                }
                if (chosen == null) {
                    chosen = frame;
                } else if (isAllZero(chosen) && !isAllZero(frame)) {
                    chosen = frame;
                }

                long active = 0L;
                double total = 0.0, sumR = 0.0, sumC = 0.0;
                int rmin = Integer.MAX_VALUE, rmax = -1, cmin = Integer.MAX_VALUE, cmax = -1;
                int H = chosen.length;
                int W = (H > 0 ? chosen[0].length : 0);
                for (int r = 0; r < H; ++r) {
                    double[] rowVec = chosen[r];
                    int colLim = Math.min(W, rowVec.length);
                    for (int c = 0; c < colLim; ++c) {
                        double value = rowVec[c];
                        if (value > 0.0) {
                            active += 1;
                            total  += value;
                            sumR   += r * value;
                            sumC   += c * value;
                            if (r < rmin) rmin = r;
                            if (r > rmax) rmax = r;
                            if (c < cmin) cmin = c;
                            if (c > cmax) cmax = c;
                        }
                    }
                }
                metrics.setActivePixels(active);
                if (total > 0.0) {
                    metrics.setCentroid(sumR / total, sumC / total);
                } else {
                    metrics.setCentroid(0.0, 0.0);
                }
                if (rmax >= rmin && cmax >= cmin) {
                    metrics.setBBox(rmin, rmax, cmin, cmax);
                } else {
                    metrics.setBBox(0, -1, 0, -1);
                }
            }
        } catch (Throwable ignored) { }
        // Best‑effort region growth (layers)
        try {
            if (growthPolicy != null) {
                GrowthEngine.maybeGrow(this, growthPolicy);
            }
        } catch (Throwable ignored) { }
        return metrics;
    }

    public RegionMetrics tickImage(String port, double[][] frame) {
        return tick2D(port, frame);
    }

    /**
     * Windowed deterministic wiring (2D). Returns number of unique participating source pixels.
     */
    public int connectLayersWindowed(
            int sourceIndex,
            int destIndex,
            int kernelHeight,
            int kernelWidth,
            int strideHeight,
            int strideWidth,
            String padding,
            boolean feedback) {
        if (sourceIndex < 0 || sourceIndex >= layers.size())
            throw new IndexOutOfBoundsException("sourceIndex out of range");
        if (destIndex < 0 || destIndex >= layers.size())
            throw new IndexOutOfBoundsException("destIndex out of range");
        if (kernelHeight <= 0 || kernelWidth <= 0)
            throw new IllegalArgumentException("kernel dims must be > 0");
        if (strideHeight <= 0 || strideWidth <= 0)
            throw new IllegalArgumentException("stride must be > 0");

        Layer src = layers.get(sourceIndex);
        Layer dst = layers.get(destIndex);

        int H = 0, W = 0;
        if (src instanceof InputLayer2D) {
            H = ((InputLayer2D) src).getHeight();
            W = ((InputLayer2D) src).getWidth();
        } else if (dst instanceof OutputLayer2D) {
            H = ((OutputLayer2D) dst).getHeight();
            W = ((OutputLayer2D) dst).getWidth();
        } else {
            int n = src.getNeurons().size();
            int side = (int)Math.sqrt(n);
            if (side * side != n) throw new IllegalStateException("source is not 2D-compatible");
            H = side; W = side;
        }

        java.util.List<int[]> origins = new java.util.ArrayList<>();
        if ("same".equalsIgnoreCase(padding)) {
            int outRows = (int)Math.ceil((double)H / strideHeight);
            int outCols = (int)Math.ceil((double)W / strideWidth);
            int padRows = Math.max(0, (outRows - 1) * strideHeight + kernelHeight - H);
            int padCols = Math.max(0, (outCols - 1) * strideWidth + kernelWidth  - W);
            int rowStart = -padRows / 2;
            int colStart = -padCols / 2;
            for (int r = rowStart; r + kernelHeight <= H + padRows; r += strideHeight) {
                for (int c = colStart; c + kernelWidth <= W + padCols; c += strideWidth) {
                    origins.add(new int[]{r, c});
                }
            }
        } else { // VALID
            for (int r = 0; r + kernelHeight <= H; r += strideHeight) {
                for (int c = 0; c + kernelWidth <= W; c += strideWidth) {
                    origins.add(new int[]{r, c});
                }
            }
        }

        java.util.Set<Integer> allowed = new java.util.HashSet<>();
        java.util.Map<Integer, Integer> centerMap = (dst instanceof OutputLayer2D)
                ? new java.util.HashMap<>() : java.util.Collections.emptyMap();

        if (dst instanceof OutputLayer2D) {
            for (int[] origin : origins) {
                int r0 = origin[0], c0 = origin[1];
                int rr0 = Math.max(0, r0), cc0 = Math.max(0, c0);
                int rr1 = Math.min(H, r0 + kernelHeight), cc1 = Math.min(W, c0 + kernelWidth);
                if (rr0 >= rr1 || cc0 >= cc1) continue;
                int cr = Math.min(H - 1, Math.max(0, r0 + kernelHeight / 2));
                int cc = Math.min(W - 1, Math.max(0, c0 + kernelWidth  / 2));
                int centerIdx = cr * W + cc;
                for (int rr = rr0; rr < rr1; ++rr) {
                    for (int cc2 = cc0; cc2 < cc1; ++cc2) {
                        int srcIdx = rr * W + cc2;
                        allowed.add(srcIdx);
                        ((java.util.Map<Integer,Integer>)centerMap).putIfAbsent(srcIdx, centerIdx);
                    }
                }
            }
            Tract tract = new Tract(src, dst, bus, feedback, allowed, centerMap);
            tracts.add(tract);
        } else {
            java.util.Set<Integer> seen = new java.util.HashSet<>();
            for (int[] origin : origins) {
                int r0 = origin[0], c0 = origin[1];
                int rr0 = Math.max(0, r0), cc0 = Math.max(0, c0);
                int rr1 = Math.min(H, r0 + kernelHeight), cc1 = Math.min(W, c0 + kernelWidth);
                if (rr0 >= rr1 || cc0 >= cc1) continue;
                for (int rr = rr0; rr < rr1; ++rr) {
                    for (int cc2 = cc0; cc2 < cc1; ++cc2) {
                        int srcIdx = rr * W + cc2;
                        if (seen.add(srcIdx)) allowed.add(srcIdx);
                    }
                }
            }
            Tract tract = new Tract(src, dst, bus, feedback, allowed, null);
            tracts.add(tract);
        }
        return allowed.size();
    }

    // ---- growth plumbing ----
    void autowireNewNeuron(Layer layerRef, int newIdx) {
        int layerIndex = layers.indexOf(layerRef); if (layerIndex < 0) return;
        // Outbound
        for (MeshRule rule : meshRules) if (rule.src == layerIndex) {
            Neuron sourceNeuron = layers.get(layerIndex).getNeurons().get(newIdx);
            for (Neuron targetNeuron : layers.get(rule.dst).getNeurons()) if (rng.nextDouble() <= rule.prob) sourceNeuron.connect(targetNeuron, rule.feedback);
        }
        // Inbound
        for (MeshRule rule : meshRules) if (rule.dst == layerIndex) {
            Neuron targetNeuron = layers.get(layerIndex).getNeurons().get(newIdx);
            for (Neuron sourceNeuron : layers.get(rule.src).getNeurons()) if (rng.nextDouble() <= rule.prob) sourceNeuron.connect(targetNeuron, rule.feedback);
        }
        // Tracts where this layer is the source: subscribe the new source neuron (if any tracts exist)
        for (Tract tractEntry : tracts) {
            if (tractEntry != null && tractEntry.getSource() == layerRef) {
                tractEntry.attachSourceNeuron(newIdx);
            }
        }
    }
    public int requestLayerGrowth(Layer saturated) {
        int layerIndex = layers.indexOf(saturated); if (layerIndex < 0) return -1;
        int newIdx = addLayer(4, 0, 0);
        // Deterministic spillover wiring (contract default): p = 1.0
        connectLayers(layerIndex, newIdx, 1.0, false);
        return newIdx;
    }

    /** Overload with explicit connection probability for saturated → new wiring. */
    public int requestLayerGrowth(Layer saturated, double connectionProbability) {
        int layerIndex = layers.indexOf(saturated); if (layerIndex < 0) return -1;
        int newIdx = addLayer(4, 0, 0);
        connectLayers(layerIndex, newIdx, connectionProbability, false);
        return newIdx;
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

    // Spatial metrics toggle
    public Region setEnableSpatialMetrics(boolean v) { this.enableSpatialMetrics = v; return this; }
    public boolean isEnableSpatialMetrics() { return enableSpatialMetrics; }

    private static boolean isAllZero(double[][] image) {
        if (image == null || image.length == 0) return true;
        for (double[] row : image) {
            for (double value : row) {
                if (value != 0.0) return false;
            }
        }
        return true;
    }

    // ------------------------------ growth policy ---------------------------
    public GrowthPolicy getGrowthPolicy() { return growthPolicy; }
    public Region setGrowthPolicy(GrowthPolicy gp) { this.growthPolicy = gp; return this; }
}
