package ai.nektron.grownet;

import ai.nektron.grownet.metrics.RegionMetrics;
import ai.nektron.grownet.growth.GrowthPolicy;
import ai.nektron.grownet.growth.GrowthEngine;

import java.util.*;

/**
 * Region: groups layers, owns wiring helpers and tick/prune orchestration.
 * Parity with C++/Python/Mojo; optional spatial metrics in tick2D.
 */
public final class Region {

    public static final class PruneSummary {
        public int prunedSynapses = 0;
        public int prunedEdges    = 0;    // reserved for future inter-layer tract pruning
    }

    private final String name;
    private final List<Layer> layers = new ArrayList<>();
    private final Map<String, List<Integer>> inputPorts  = new HashMap<>();
    private final Map<String, List<Integer>> outputPorts = new HashMap<>();
    private final Map<String, Integer> inputEdges = new HashMap<>();
    private final Map<String, Integer> outputEdges = new HashMap<>();
    private final RegionBus bus = new RegionBus();
    private final Random rng = new Random(1234);
    private final List<MeshRule> meshRules = new ArrayList<>();
    private final List<Tract> tracts = new ArrayList<>();

    private boolean enableSpatialMetrics = false;
    private GrowthPolicy growthPolicy = null;

    private static final class MeshRule {
        final int src, dst; final double prob; final boolean feedback;
        MeshRule(int s, int d, double p, boolean f) { src=s; dst=d; prob=p; feedback=f; }
    }

    public Region(String name) { this.name = name; }

    public int addLayer(int excitatoryCount, int inhibitoryCount, int modulatoryCount) {
        Layer layer = new Layer(excitatoryCount, inhibitoryCount, modulatoryCount);
        try { layer.setRegion(this); } catch (Throwable ignored) {}
        layers.add(layer);
        return layers.size() - 1;
    }

    public int addInputLayer2D(int height, int width, double gain, double epsilonFire) {
        InputLayer2D in = new InputLayer2D(height, width, gain, epsilonFire);
        layers.add(in);
        return layers.size() - 1;
    }

    public int addOutputLayer2D(int height, int width, double smoothing) {
        OutputLayer2D out = new OutputLayer2D(height, width, smoothing);
        layers.add(out);
        return layers.size() - 1;
    }

    private int ensureInputEdge(String port) {
        Integer idx = inputEdges.get(port);
        if (idx != null) return idx;
        int edge = addLayer(1, 0, 0);
        inputEdges.put(port, edge);
        return edge;
    }

    private int ensureOutputEdge(String port) {
        Integer idx = outputEdges.get(port);
        if (idx != null) return idx;
        int edge = addLayer(1, 0, 0);
        outputEdges.put(port, edge);
        return edge;
    }

    public int connectLayers(int sourceIndex, int destIndex, double probability, boolean feedback) {
        if (sourceIndex < 0 || sourceIndex >= layers.size()) throw new IndexOutOfBoundsException("sourceIndex out of range");
        if (destIndex < 0 || destIndex >= layers.size()) throw new IndexOutOfBoundsException("destIndex out of range");
        if (probability < 0.0) probability = 0.0; if (probability > 1.0) probability = 1.0;
        Layer src = layers.get(sourceIndex);
        Layer dst = layers.get(destIndex);
        int edges = 0;
        for (Neuron neuronA : src.getNeurons()) {
            for (Neuron neuronB : dst.getNeurons()) {
                if (neuronA == neuronB) continue;
                if (rng.nextDouble() < probability) { neuronA.connect(neuronB, feedback); edges++; }
            }
        }
        meshRules.add(new MeshRule(sourceIndex, destIndex, probability, feedback));
        return edges;
    }

    public void bindInput(String port, List<Integer> layerIndices) {
        Objects.requireNonNull(port, "port");
        Objects.requireNonNull(layerIndices, "layerIndices");
        inputPorts.put(port, List.copyOf(layerIndices));
        int edge = ensureInputEdge(port);
        for (int layerIndex : layerIndices) connectLayers(edge, layerIndex, 1.0, false);
    }

    public void bindOutput(String port, List<Integer> layerIndices) {
        Objects.requireNonNull(port, "port");
        Objects.requireNonNull(layerIndices, "layerIndices");
        outputPorts.put(port, List.copyOf(layerIndices));
        int edge = ensureOutputEdge(port);
        for (int layerIndex : layerIndices) connectLayers(layerIndex, edge, 1.0, false);
    }

    public void bindInput2D(String port, int height, int width, double gain, double epsilonFire, List<Integer> layerIndices) {
        Objects.requireNonNull(port, "port");
        Objects.requireNonNull(layerIndices, "layerIndices");
        Integer idx = inputEdges.get(port);
        boolean needNew2D = true;
        if (idx != null) needNew2D = !(layers.get(idx) instanceof InputLayer2D);
        if (idx == null || needNew2D) {
            int edgeIndex = addInputLayer2D(height, width, gain, epsilonFire);
            inputEdges.put(port, edgeIndex);
            idx = edgeIndex;
        }
        inputPorts.put(port, List.copyOf(layerIndices));
        for (int layerIndex : layerIndices) connectLayers(idx, layerIndex, 1.0, false);
    }

    public RegionMetrics tick(String port, double value) {
        RegionMetrics metrics = new RegionMetrics();
        Integer edgeIdx = inputEdges.get(port);
        if (edgeIdx == null) throw new IllegalArgumentException("No InputEdge for port '" + port + "'. Call bindInput(...) first.");
        layers.get(edgeIdx).forward(value);
        metrics.incDeliveredEvents();
        for (Layer l : layers) l.endTick();
        bus.decay();
        for (Layer l : layers) for (Neuron n : l.getNeurons()) { metrics.addSlots(n.getSlots().size()); metrics.addSynapses(n.getOutgoing().size()); }
        try { if (growthPolicy != null) { GrowthEngine.maybeGrowNeurons(this, growthPolicy); GrowthEngine.maybeGrow(this, growthPolicy); } } catch (Throwable ignored) { }
        return metrics;
    }

    public RegionMetrics tick2D(String port, double[][] frame) {
        RegionMetrics metrics = new RegionMetrics();
        Integer edge = inputEdges.get(port);
        if (edge == null) throw new IllegalArgumentException("No InputEdge for port '" + port + "'. Call bindInput2D(...) first.");
        Layer layer = layers.get(edge);
        if (!(layer instanceof InputLayer2D)) throw new IllegalArgumentException("InputEdge for '" + port + "' is not 2D (expected InputLayer2D).");
        ((InputLayer2D) layer).forwardImage(frame);
        metrics.incDeliveredEvents();
        for (Layer l : layers) l.endTick();
        bus.decay();
        for (Layer l : layers) for (Neuron n : l.getNeurons()) { metrics.addSlots(n.getSlots().size()); metrics.addSynapses(n.getOutgoing().size()); }
        try {
            String env = System.getenv("GROWNET_ENABLE_SPATIAL_METRICS");
            boolean doSpatial = enableSpatialMetrics || "1".equals(env);
            if (doSpatial) {
                double[][] chosen = null;
                for (int i = layers.size() - 1; i >= 0; --i) {
                    Layer L = layers.get(i);
                    if (L instanceof OutputLayer2D) { chosen = ((OutputLayer2D) L).getFrame(); break; }
                }
                if (chosen == null) chosen = frame; else if (isAllZero(chosen) && !isAllZero(frame)) chosen = frame;
                long active = 0L; double total = 0.0, sumR = 0.0, sumC = 0.0;
                int rmin = Integer.MAX_VALUE, rmax = -1, cmin = Integer.MAX_VALUE, cmax = -1;
                int H = chosen.length; int W = (H > 0 ? chosen[0].length : 0);
                for (int r = 0; r < H; ++r) {
                    double[] row = chosen[r]; int colLim = Math.min(W, row.length);
                    for (int c = 0; c < colLim; ++c) {
                        double v = row[c]; if (v > 0.0) { active += 1; total += v; sumR += r * v; sumC += c * v; if (r < rmin) rmin = r; if (r > rmax) rmax = r; if (c < cmin) cmin = c; if (c > cmax) cmax = c; }
                    }
                }
                metrics.setActivePixels(active);
                if (total > 0.0) metrics.setCentroid(sumR / total, sumC / total); else metrics.setCentroid(0.0, 0.0);
                if (rmax >= rmin && cmax >= cmin) metrics.setBBox(rmin, rmax, cmin, cmax); else metrics.setBBox(0, -1, 0, -1);
            }
        } catch (Throwable ignored) { }
        try { if (growthPolicy != null) GrowthEngine.maybeGrow(this, growthPolicy); } catch (Throwable ignored) { }
        return metrics;
    }

    public RegionMetrics tickImage(String port, double[][] frame) { return tick2D(port, frame); }

    // --- wiring helper (tract + mesh rules) is present in full code; omitted here for brevity ---

    public String getName() { return name; }
    public List<Layer> getLayers() { return layers; }
    public RegionBus getBus() { return bus; }
    public Region setEnableSpatialMetrics(boolean v) { this.enableSpatialMetrics = v; return this; }
    public boolean isEnableSpatialMetrics() { return enableSpatialMetrics; }

    private static boolean isAllZero(double[][] image) {
        if (image == null || image.length == 0) return true;
        for (double[] row : image) for (double value : row) if (value != 0.0) return false;
        return true;
    }
}

