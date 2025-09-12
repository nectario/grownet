package ai.nektron.grownet.preset;

import ai.nektron.grownet.InputLayer2D;
import ai.nektron.grownet.OutputLayer2D;
import ai.nektron.grownet.Region;

import java.util.*;

/** Topographic wiring preset: wraps connectLayersWindowed, computes deterministic weights. */
public final class TopographicWiring {

    private TopographicWiring() {}

    public static int connectLayersTopographic(Region region, int srcIndex, int dstIndex, TopographicConfig cfg) {
        validate(cfg);
        int uniqueSources = region.connectLayersWindowed(
                srcIndex, dstIndex,
                cfg.kernelH, cfg.kernelW,
                cfg.strideH, cfg.strideW,
                cfg.padding, cfg.feedback);

        // Geometry (2D only)
        int Hs = 0, Ws = 0, Hd = 0, Wd = 0;
        if (region.getLayers().get(srcIndex) instanceof InputLayer2D) {
            InputLayer2D in = (InputLayer2D) region.getLayers().get(srcIndex);
            Hs = in.getHeight(); Ws = in.getWidth();
        }
        if (region.getLayers().get(dstIndex) instanceof OutputLayer2D) {
            OutputLayer2D out = (OutputLayer2D) region.getLayers().get(dstIndex);
            Hd = out.getHeight(); Wd = out.getWidth();
        }
        if (Hs <= 0 || Ws <= 0 || Hd <= 0 || Wd <= 0) {
            throw new IllegalArgumentException("Topographic wiring requires 2D source and destination layers");
        }

        // Reconstruct mapping and compute weights
        Map<Integer, Double> incomingSums = new HashMap<>();
        Map<Long, Double> weights = new HashMap<>(); // key = ((long)src<<32)|dst

        List<int[]> windowOrigins = new ArrayList<>();
        boolean useSamePadding = "same".equalsIgnoreCase(cfg.padding);
        if (useSamePadding) {
            int padRows = Math.max(0, (cfg.kernelH - 1) / 2);
            int padCols = Math.max(0, (cfg.kernelW - 1) / 2);
            for (int originRow = -padRows; originRow + cfg.kernelH <= Hs + padRows + padRows; originRow += cfg.strideH) {
                for (int originCol = -padCols; originCol + cfg.kernelW <= Ws + padCols + padCols; originCol += cfg.strideW) {
                    windowOrigins.add(new int[]{originRow, originCol});
                }
            }
        } else {
            for (int originRow = 0; originRow + cfg.kernelH <= Hs; originRow += cfg.strideH) {
                for (int originCol = 0; originCol + cfg.kernelW <= Ws; originCol += cfg.strideW) {
                    windowOrigins.add(new int[]{originRow, originCol});
                }
            }
        }

        for (int[] origin : windowOrigins) {
            int originRow = origin[0];
            int originCol = origin[1];
            int rowStart = Math.max(0, originRow);
            int colStart = Math.max(0, originCol);
            int rowEnd = Math.min(Hs, originRow + cfg.kernelH);
            int colEnd = Math.min(Ws, originCol + cfg.kernelW);
            if (rowStart >= rowEnd || colStart >= colEnd) continue;
            int centerRow = Math.min(Hs - 1, Math.max(0, originRow + cfg.kernelH / 2));
            int centerCol = Math.min(Ws - 1, Math.max(0, originCol + cfg.kernelW / 2));
            int centerIndex = centerRow * Wd + centerCol;
            for (int srcRow = rowStart; srcRow < rowEnd; ++srcRow) {
                for (int srcCol = colStart; srcCol < colEnd; ++srcCol) {
                    int sourceFlat = srcRow * Ws + srcCol;
                    double deltaRow = (double) (srcRow - centerRow);
                    double deltaCol = (double) (srcCol - centerCol);
                    double squaredDistance = deltaRow * deltaRow + deltaCol * deltaCol;
                    double w;
                    if ("dog".equalsIgnoreCase(cfg.weightMode)) {
                        double weightCenter = Math.exp(-squaredDistance / (2.0 * cfg.sigmaCenter * cfg.sigmaCenter));
                        double weightSurround = Math.exp(-squaredDistance / (2.0 * cfg.sigmaSurround * cfg.sigmaSurround));
                        w = Math.max(0.0, weightCenter - cfg.surroundRatio * weightSurround);
                    } else {
                        w = Math.exp(-squaredDistance / (2.0 * cfg.sigmaCenter * cfg.sigmaCenter));
                    }
                    long key = (((long) sourceFlat) << 32) | (centerIndex & 0xffffffffL);
                    if (!weights.containsKey(key)) {
                        weights.put(key, w);
                        incomingSums.put(centerIndex, incomingSums.getOrDefault(centerIndex, 0.0) + w);
                    }
                }
            }
        }

        if (cfg.normalizeIncoming) {
            for (Map.Entry<Long, Double> e : new ArrayList<>(weights.entrySet())) {
                long key = e.getKey();
                int centerIndex = (int) (key & 0xffffffffL);
                double sum = incomingSums.getOrDefault(centerIndex, 0.0);
                if (sum > 1e-12) {
                    weights.put(key, e.getValue() / sum);
                }
            }
        }

        // Stored weights are not applied to runtime edges in this Java variant (tract-based delivery);
        // callers can use helper to inspect incoming sums deterministically.
        Registry.put(region, srcIndex, dstIndex, weights);
        return uniqueSources;
    }

    public static double[] incomingSums(Region region, int dstIndex) {
        int Hd = 0, Wd = 0;
        if (region.getLayers().get(dstIndex) instanceof OutputLayer2D) {
            OutputLayer2D out = (OutputLayer2D) region.getLayers().get(dstIndex);
            Hd = out.getHeight(); Wd = out.getWidth();
        }
        double[] sums = new double[Math.max(1, Hd * Wd)];
        Map<Long, Double> weights = Registry.getAll(region);
        if (weights != null) {
            for (Map.Entry<Long, Double> e : weights.entrySet()) {
                int centerIndex = (int) (e.getKey() & 0xffffffffL);
                if (centerIndex >= 0 && centerIndex < sums.length) {
                    sums[centerIndex] += e.getValue();
                }
            }
        }
        return sums;
    }

    private static void validate(TopographicConfig cfg) {
        if (cfg.kernelH < 1 || cfg.kernelW < 1) throw new IllegalArgumentException("kernel dims must be >= 1");
        if (cfg.strideH < 1 || cfg.strideW < 1) throw new IllegalArgumentException("stride must be >= 1");
        if (!"same".equalsIgnoreCase(cfg.padding) && !"valid".equalsIgnoreCase(cfg.padding))
            throw new IllegalArgumentException("padding must be 'same' or 'valid'");
        if (cfg.sigmaCenter <= 0.0) throw new IllegalArgumentException("sigmaCenter must be > 0");
        if ("dog".equalsIgnoreCase(cfg.weightMode)) {
            if (cfg.sigmaSurround <= cfg.sigmaCenter)
                throw new IllegalArgumentException("sigmaSurround must be > sigmaCenter for DoG");
            if (cfg.surroundRatio < 0.0)
                throw new IllegalArgumentException("surroundRatio must be >= 0");
        }
    }

    // lightweight per-region registry for demo/tests (no core changes)
    private static final class Registry {
        private static final Map<Integer, Map<Long, Double>> map = new HashMap<>();
        static void put(Region region, int src, int dst, Map<Long, Double> weights) {
            int key = Objects.hash(System.identityHashCode(region), src, dst);
            map.put(key, new HashMap<>(weights));
        }
        static Map<Long, Double> get(Region region, int src, int dst) {
            int key = Objects.hash(System.identityHashCode(region), src, dst);
            return map.get(key);
        }
        static Map<Long, Double> getAll(Region region) {
            // demo helper: return latest entry for this region
            Map.Entry<Integer, Map<Long, Double>> last = null;
            for (Map.Entry<Integer, Map<Long, Double>> e : map.entrySet()) last = e;
            return (last == null ? null : last.getValue());
        }
    }
}
