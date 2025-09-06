package ai.nektron.grownet;

import ai.nektron.grownet.metrics.RegionMetrics;
import java.util.*;

public final class Region {
    private final String name;
    private final List<Layer> layers = new ArrayList<>();
    private final Map<String, Integer> inputEdges = new HashMap<>();
    private final List<Tract> tracts = new ArrayList<>();
    private final List<MeshRule> meshRules = new ArrayList<>();
    private final RegionBus bus = new RegionBus();
    private boolean enableSpatialMetrics = false;

    private static final class MeshRule { final int src, dst; final double prob; final boolean feedback; MeshRule(int s,int d,double p,boolean f){src=s;dst=d;prob=p;feedback=f;} }

    public Region(String name) { this.name = name; }

    public int addLayer(int excitatoryCount, int inhibitoryCount, int modulatoryCount) {
        Layer layer = new Layer(excitatoryCount, inhibitoryCount, modulatoryCount);
        try { layer.setRegion(this); } catch (Throwable ignored) {}
        layers.add(layer);
        return layers.size() - 1;
    }

    public int addInputLayer2D(int height, int width, double gain, double epsilonFire) {
        layers.add(new InputLayer2D(height, width, gain, epsilonFire));
        return layers.size() - 1;
    }

    public int addOutputLayer2D(int height, int width, double smoothing) {
        layers.add(new OutputLayer2D(height, width, smoothing));
        return layers.size() - 1;
    }

    public int connectLayers(int sourceIndex, int destIndex, double probability, boolean feedback) {
        Layer src = layers.get(sourceIndex), dst = layers.get(destIndex);
        int edges = 0; Random rng = new Random(1234);
        for (Neuron a : src.getNeurons()) for (Neuron b : dst.getNeurons()) if (a!=b && rng.nextDouble()<probability) { a.connect(b, feedback); edges++; }
        meshRules.add(new MeshRule(sourceIndex, destIndex, probability, feedback));
        return edges;
    }

    public void bindInput2D(String port, int height, int width, double gain, double epsilonFire, List<Integer> layerIndices) {
        Integer idx = inputEdges.get(port);
        boolean needNew2D = true;
        if (idx != null) needNew2D = !(layers.get(idx) instanceof InputLayer2D);
        if (idx == null || needNew2D) {
            int edgeIndex = addInputLayer2D(height, width, gain, epsilonFire);
            inputEdges.put(port, edgeIndex);
            idx = edgeIndex;
        }
        for (int layerIndex : layerIndices) connectLayers(idx, layerIndex, 1.0, false);
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
                for (int i = layers.size() - 1; i >= 0; --i) if (layers.get(i) instanceof OutputLayer2D) { chosen = ((OutputLayer2D) layers.get(i)).getFrame(); break; }
                if (chosen == null) chosen = frame; else if (isAllZero(chosen) && !isAllZero(frame)) chosen = frame;
                long active = 0L; double total = 0.0, sumR = 0.0, sumC = 0.0;
                int rmin = Integer.MAX_VALUE, rmax = -1, cmin = Integer.MAX_VALUE, cmax = -1;
                int H = chosen.length, W = (H > 0 ? chosen[0].length : 0);
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
        return metrics;
    }

    public int connectLayersWindowed(int sourceIndex, int destIndex, int kernelH, int kernelW, int strideH, int strideW, String padding, boolean feedback) {
        Layer src = layers.get(sourceIndex), dst = layers.get(destIndex);
        int H = (src instanceof InputLayer2D) ? ((InputLayer2D) src).getHeight() : ((dst instanceof OutputLayer2D) ? ((OutputLayer2D) dst).getHeight() : 0);
        int W = (src instanceof InputLayer2D) ? ((InputLayer2D) src).getWidth()  : ((dst instanceof OutputLayer2D) ? ((OutputLayer2D) dst).getWidth()  : 0);
        List<int[]> origins = new ArrayList<>(); boolean useSame = "same".equalsIgnoreCase(padding);
        if (useSame) { int padR = Math.max(0, (kernelH - 1) / 2), padC = Math.max(0, (kernelW - 1) / 2);
            for (int r0 = -padR; r0 + kernelH <= H + padR + padR; r0 += strideH) for (int c0 = -padC; c0 + kernelW <= W + padC + padC; c0 += strideW) origins.add(new int[]{r0, c0});
        } else { for (int r0 = 0; r0 + kernelH <= H; r0 += strideH) for (int c0 = 0; c0 + kernelW <= W; c0 += strideW) origins.add(new int[]{r0, c0}); }
        Set<Integer> allowed = new HashSet<>(); Map<Integer,Integer> centerMap = (dst instanceof OutputLayer2D) ? new HashMap<>() : Collections.emptyMap();
        if (dst instanceof OutputLayer2D) {
            for (int[] origin : origins) {
                int r0 = origin[0], c0 = origin[1]; int rr0 = Math.max(0, r0), cc0 = Math.max(0, c0); int rr1 = Math.min(H, r0 + kernelH), cc1 = Math.min(W, c0 + kernelW); if (rr0 >= rr1 || cc0 >= cc1) continue;
                int cr = Math.min(H - 1, Math.max(0, r0 + kernelH / 2)), cc = Math.min(W - 1, Math.max(0, c0 + kernelW  / 2)); int centerIdx = cr * W + cc;
                for (int rr = rr0; rr < rr1; ++rr) for (int cc2 = cc0; cc2 < cc1; ++cc2) { int srcIdx = rr * W + cc2; allowed.add(srcIdx); ((Map<Integer,Integer>)centerMap).putIfAbsent(srcIdx, centerIdx); }
            }
            tracts.add(new Tract(src, dst, bus, feedback, allowed, centerMap));
        } else {
            Set<Integer> seen = new HashSet<>();
            for (int[] origin : origins) { int r0 = origin[0], c0 = origin[1]; int rr0 = Math.max(0, r0), cc0 = Math.max(0, c0); int rr1 = Math.min(H, r0 + kernelH), cc1 = Math.min(W, c0 + kernelW); if (rr0 >= rr1 || cc0 >= cc1) continue;
                for (int rr = rr0; rr < rr1; ++rr) for (int cc2 = cc0; cc2 < cc1; ++cc2) { int srcIdx = rr * W + cc2; if (seen.add(srcIdx)) allowed.add(srcIdx); }
            }
            tracts.add(new Tract(src, dst, bus, feedback, allowed, null));
        }
        return allowed.size();
    }

    public Region setEnableSpatialMetrics(boolean v) { this.enableSpatialMetrics = v; return this; }
    public boolean isEnableSpatialMetrics() { return enableSpatialMetrics; }
    public List<Layer> getLayers() { return layers; }
    public RegionBus getBus() { return bus; }
    public String getName() { return name; }

    private static boolean isAllZero(double[][] image) {
        if (image == null || image.length == 0) return true;
        for (double[] row : image) for (double value : row) if (value != 0.0) return false;
        return true;
    }
}

