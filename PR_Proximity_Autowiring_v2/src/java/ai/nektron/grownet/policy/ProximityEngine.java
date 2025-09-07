// File: src/java/ai/nektron/grownet/policy/ProximityEngine.java
// NOTE: ADAPT region API calls to your codebase.
package ai.nektron.grownet.policy;

import java.util.*;

public final class ProximityEngine {

    private static final class RegionState {
        final Map<String, Long> lastAttemptByNeuron = new HashMap<>();
    }

    private static final Map<String, RegionState> stateByRegion = new HashMap<>();

    private static String regionKey(Object region) {
        try {
            return (String) region.getClass().getMethod("getName").invoke(region);
        } catch (Exception reflectionError) {
            return "region_" + System.identityHashCode(region);
        }
    }

    public static int apply(Object region, ProximityConfig config) {
        if (!config.proximityConnectEnabled) return 0;
        long currentStep = getCurrentStep(region);
        if (currentStep < config.developmentWindowStart || currentStep > config.developmentWindowEnd) return 0;

        String key = regionKey(region);
        RegionState state = stateByRegion.computeIfAbsent(key, k -> new RegionState());

        List<Integer> candidateLayers = getCandidateLayers(region, config);

        SpatialHash<int[]> grid = new SpatialHash<>(config.proximityRadius);
        for (int layerIndex : candidateLayers) {
            int layerHeight = getLayerHeight(region, layerIndex);
            int layerWidth  = getLayerWidth(region, layerIndex);
            int neuronCount = getNeuronCount(region, layerIndex);
            for (int neuronIndex = 0; neuronIndex < neuronCount; neuronIndex++) {
                double[] pos = DeterministicLayout.position(key, layerIndex, neuronIndex, layerHeight, layerWidth);
                grid.insert(new int[]{layerIndex, neuronIndex}, pos);
            }
        }

        Random regionRandom = getRegionRandom(region);
        int edgesAdded = 0;

        for (int layerIndex : candidateLayers) {
            int layerHeight = getLayerHeight(region, layerIndex);
            int layerWidth  = getLayerWidth(region, layerIndex);
            int neuronCount = getNeuronCount(region, layerIndex);
            for (int neuronIndex = 0; neuronIndex < neuronCount; neuronIndex++) {
                String neuronKey = layerIndex + ":" + neuronIndex;
                long lastAttempt = state.lastAttemptByNeuron.getOrDefault(neuronKey, Long.MIN_VALUE);
                if ((currentStep - lastAttempt) < config.proximityCooldownTicks) continue;

                double[] origin = DeterministicLayout.position(key, layerIndex, neuronIndex, layerHeight, layerWidth);
                for (int[] neighbor : grid.near(origin)) {
                    int neighborLayerIndex = neighbor[0];
                    int neighborNeuronIndex = neighbor[1];
                    if (neighborLayerIndex == layerIndex && neighborNeuronIndex == neuronIndex) continue;
                    if (alreadyConnected(region, layerIndex, neuronIndex, neighborLayerIndex, neighborNeuronIndex)) continue;

                    int nh = getLayerHeight(region, neighborLayerIndex);
                    int nw = getLayerWidth(region, neighborLayerIndex);
                    double[] neighborPos = DeterministicLayout.position(key, neighborLayerIndex, neighborNeuronIndex, nh, nw);
                    double distanceValue = euclideanDistance(origin, neighborPos);
                    if (distanceValue > config.proximityRadius) continue;

                    double probabilityValue = probabilityFromDistance(distanceValue, config);
                    if (probabilityValue < 1.0) {
                        if (regionRandom == null) {
                            throw new RuntimeException("ProximityEngine: probabilistic mode requires a seeded region RNG");
                        }
                        if (regionRandom.nextDouble() >= probabilityValue) continue;
                    }
                    connectNeurons(region, layerIndex, neuronIndex, neighborLayerIndex, neighborNeuronIndex, config.recordMeshRulesOnCrossLayer);
                    state.lastAttemptByNeuron.put(neuronKey, currentStep);
                    state.lastAttemptByNeuron.put(neighborLayerIndex + ":" + neighborNeuronIndex, currentStep);
                    edgesAdded += 1;
                    if (edgesAdded >= config.proximityMaxEdgesPerTick) return edgesAdded;
                }
            }
        }
        return edgesAdded;
    }

    private static double probabilityFromDistance(double distance, ProximityConfig cfg) {
        if ("STEP".equals(cfg.proximityFunction)) return (distance <= cfg.proximityRadius) ? 1.0 : 0.0;
        double unit = Math.max(0.0, 1.0 - distance / Math.max(cfg.proximityRadius, 1e-12));
        if ("LINEAR".equals(cfg.proximityFunction)) return Math.pow(unit, Math.max(cfg.linearExponentGamma, 1e-12));
        return 1.0 / (1.0 + Math.exp(cfg.logisticSteepnessK * (distance - cfg.proximityRadius)));
    }

    private static double euclideanDistance(double[] a, double[] b) {
        double dx = a[0] - b[0], dy = a[1] - b[1], dz = a[2] - b[2];
        return Math.sqrt(dx*dx + dy*dy + dz*dz);
    }

    // ===== ADAPT region API calls below to your codebase =====
    private static long getCurrentStep(Object region) {
        try { return (long) region.getClass().getMethod("getCurrentStep").invoke(region); } catch (Exception ignore) {}
        try { Object bus = region.getClass().getMethod("bus").invoke(region);
              return (long) bus.getClass().getMethod("getCurrentStep").invoke(bus); } catch (Exception e) { return 0L; }
    }

    private static List<Integer> getCandidateLayers(Object region, ProximityConfig cfg) {
        if (cfg.candidateLayers != null && cfg.candidateLayers.length > 0) {
            List<Integer> list = new ArrayList<>();
            for (int v : cfg.candidateLayers) list.add(v);
            return list;
        }
        int count = getLayerCount(region);
        List<Integer> all = new ArrayList<>(count);
        for (int idx = 0; idx < count; idx++) all.add(idx);
        return all;
    }

    private static int getLayerCount(Object region) {
        try { return (int) region.getClass().getMethod("layerCount").invoke(region); }
        catch (Exception e) { throw new RuntimeException("ADAPT: implement layerCount()"); }
    }

    private static int getNeuronCount(Object region, int layerIndex) {
        try { Object layer = region.getClass().getMethod("layer", int.class).invoke(region, layerIndex);
              return (int) layer.getClass().getMethod("getNeuronCount").invoke(layer); }
        catch (Exception e) { throw new RuntimeException("ADAPT: implement getNeuronCount()"); }
    }

    private static int getLayerHeight(Object region, int layerIndex) {
        try { Object layer = region.getClass().getMethod("layer", int.class).invoke(region, layerIndex);
              return (int) layer.getClass().getMethod("getHeight").invoke(layer); }
        catch (Exception e) { return 0; }
    }

    private static int getLayerWidth(Object region, int layerIndex) {
        try { Object layer = region.getClass().getMethod("layer", int.class).invoke(region, layerIndex);
              return (int) layer.getClass().getMethod("getWidth").invoke(layer); }
        catch (Exception e) { return 0; }
    }

    private static Random getRegionRandom(Object region) {
        try { return (Random) region.getClass().getMethod("getRng").invoke(region); }
        catch (Exception e) { return null; }
    }

    private static boolean alreadyConnected(Object region, int sl, int sn, int dl, int dn) {
        try {
            return (boolean) region.getClass().getMethod("hasEdge", int.class, int.class, int.class, int.class)
                .invoke(region, sl, sn, dl, dn);
        } catch (Exception e) {
            // Fallback: scan
            // ADAPT: expose a reliable way to scan outgoing synapses and check target layer/index.
            return false;
        }
    }

    private static void connectNeurons(Object region, int sl, int sn, int dl, int dn, boolean recordRule) {
        try {
            region.getClass().getMethod("connectNeurons", int.class, int.class, int.class, int.class, boolean.class)
                .invoke(region, sl, sn, dl, dn, false);
        } catch (Exception e) {
            throw new RuntimeException("ADAPT: implement connectNeurons(...)");
        }
        if (recordRule && sl != dl) {
            try {
                region.getClass().getMethod("recordMeshRuleFor", int.class, int.class, double.class, boolean.class)
                    .invoke(region, sl, dl, 1.0, false);
            } catch (Exception ignore) {}
        }
    }
}
