package ai.nektron.grownet.policy;

import ai.nektron.grownet.Layer;
import ai.nektron.grownet.Neuron;
import ai.nektron.grownet.Region;

import java.util.*;

public final class ProximityEngine {

    private ProximityEngine() { }

    private static final Map<String, Map<String, Long>> regionCooldown = new HashMap<>();

    private static String keyOf(int layerIndex, int neuronIndex) {
        return layerIndex + ":" + neuronIndex;
    }

    public static int apply(Region region, ProximityConfig config) {
        if (region == null || config == null) return 0;
        if (!config.isEnabled()) return 0;
        if (!(config.getRadius() > 0.0)) return 0;

        long step = 0L;
        try { step = region.getBus().getCurrentStep(); } catch (Throwable ignored) { }
        if (step < config.getDevelopmentWindowStart() || step > config.getDevelopmentWindowEnd()) return 0;

        List<Layer> layers = region.getLayers();
        Set<Integer> candidates = config.getCandidateLayers();
        List<Integer> candidateIndices = new ArrayList<>();
        if (candidates == null || candidates.isEmpty()) {
            for (int i = 0; i < layers.size(); ++i) candidateIndices.add(i);
        } else {
            candidateIndices.addAll(candidates);
        }
        if (candidateIndices.isEmpty()) return 0;

        SpatialHash grid = new SpatialHash(config.getRadius());
        String regionName = region.getName();
        for (int layerIndex : candidateIndices) {
            Layer L = layers.get(layerIndex);
            int h = 0, w = 0;
            try { h = (int) L.getClass().getMethod("getHeight").invoke(L); } catch (Throwable ignored) { }
            try { w = (int) L.getClass().getMethod("getWidth").invoke(L); } catch (Throwable ignored) { }
            List<Neuron> neurons = L.getNeurons();
            for (int neuronIndex = 0; neuronIndex < neurons.size(); ++neuronIndex) {
                double[] pos = DeterministicLayout.position(regionName, layerIndex, neuronIndex, h, w);
                grid.insert(layerIndex, neuronIndex, pos);
            }
        }

        Map<String, Long> last = regionCooldown.computeIfAbsent(regionName, k -> new HashMap<>());
        int edgesAdded = 0;
        final int cooldownTicks = Math.max(0, config.getCooldownTicks());
        for (int layerIndex : candidateIndices) {
            Layer L = layers.get(layerIndex);
            int h = 0, w = 0;
            try { h = (int) L.getClass().getMethod("getHeight").invoke(L); } catch (Throwable ignored) { }
            try { w = (int) L.getClass().getMethod("getWidth").invoke(L); } catch (Throwable ignored) { }
            List<Neuron> neurons = L.getNeurons();
            for (int neuronIndex = 0; neuronIndex < neurons.size(); ++neuronIndex) {
                String key = keyOf(layerIndex, neuronIndex);
                long prev = last.getOrDefault(key, Long.MIN_VALUE / 4);
                if ((step - prev) < cooldownTicks) continue;
                // Mark an attempt time even if we end up adding no edges for this source this tick,
                // so cooldown applies across consecutive applications.
                last.put(key, step);
                double[] origin = DeterministicLayout.position(regionName, layerIndex, neuronIndex, h, w);
                for (int[] pair : grid.near(origin)) {
                    int neighborLayer = pair[0];
                    int neighborNeuron = pair[1];
                    if (neighborLayer == layerIndex && neighborNeuron == neuronIndex) continue;
                    // Use same-layer only for now (cross-layer connect is possible but mesh-rule recording not added)
                    // It is allowed to remove this restriction if desired.
                    // Compute distance
                    Layer Ln = layers.get(neighborLayer);
                    int hn = 0, wn = 0;
                    try { hn = (int) Ln.getClass().getMethod("getHeight").invoke(Ln); } catch (Throwable ignored) { }
                    try { wn = (int) Ln.getClass().getMethod("getWidth").invoke(Ln); } catch (Throwable ignored) { }
                    double[] neighbor = DeterministicLayout.position(regionName, neighborLayer, neighborNeuron, hn, wn);
                    double ox = origin[0] - neighbor[0];
                    double oy = origin[1] - neighbor[1];
                    double oz = origin[2] - neighbor[2];
                    double distance = Math.sqrt(ox * ox + oy * oy + oz * oz);
                    if (distance > config.getRadius()) continue;
                    // STEP only unless Region exposes RNG; for LINEAR/LOGISTIC we would need seeded region RNG
                    if (!"STEP".equalsIgnoreCase(config.getFunction())) {
                        throw new IllegalStateException("ProximityEngine: probabilistic modes require Region RNG; use STEP");
                    }
                    Neuron src = L.getNeurons().get(neuronIndex);
                    Neuron dst = layers.get(neighborLayer).getNeurons().get(neighborNeuron);
                    // has_edge fallback
                    boolean already = false;
                    for (ai.nektron.grownet.Synapse syn : src.getOutgoing()) {
                        if (syn.getTarget() == dst) { already = true; break; }
                    }
                    if (already) continue;
                    src.connect(dst, false);
                    last.put(keyOf(neighborLayer, neighborNeuron), step);
                    edgesAdded++;
                    if (edgesAdded >= Math.max(0, config.getMaxEdgesPerTick())) return edgesAdded;
                }
            }
        }
        return edgesAdded;
    }
}
