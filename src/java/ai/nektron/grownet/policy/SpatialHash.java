package ai.nektron.grownet.policy;

import java.util.*;

public final class SpatialHash {
    private final double cellSize;
    private final Map<Long, List<int[]>> cells = new HashMap<>();

    public SpatialHash(double cellSize) {
        if (!(cellSize > 0.0)) throw new IllegalArgumentException("cellSize must be > 0");
        this.cellSize = cellSize;
    }

    private static long pack(int x, int y, int z) {
        return (((long) x) & 0x1FFFFFL) | ((((long) y) & 0x1FFFFFL) << 21) | ((((long) z) & 0x1FFFFFL) << 42);
    }

    private long keyForPosition(double[] p) {
        int kx = (int) Math.floor(p[0] / cellSize);
        int ky = (int) Math.floor(p[1] / cellSize);
        int kz = (int) Math.floor(p[2] / cellSize);
        return pack(kx, ky, kz);
    }

    public void insert(int layerIndex, int neuronIndex, double[] pos) {
        long key = keyForPosition(pos);
        cells.computeIfAbsent(key, k -> new ArrayList<>()).add(new int[] { layerIndex, neuronIndex });
    }

    public Iterable<int[]> near(double[] pos) {
        List<int[]> out = new ArrayList<>();
        long base = keyForPosition(pos);
        // unpack the base back into ints (approximate by recomputing)
        int baseX = (int) Math.floor(pos[0] / cellSize);
        int baseY = (int) Math.floor(pos[1] / cellSize);
        int baseZ = (int) Math.floor(pos[2] / cellSize);
        for (int oz = -1; oz <= 1; oz++) {
            for (int oy = -1; oy <= 1; oy++) {
                for (int ox = -1; ox <= 1; ox++) {
                    long neighborKey = pack(baseX + ox, baseY + oy, baseZ + oz);
                    List<int[]> bucket = cells.get(neighborKey);
                    if (bucket != null) out.addAll(bucket);
                }
            }
        }
        return out;
    }
}

