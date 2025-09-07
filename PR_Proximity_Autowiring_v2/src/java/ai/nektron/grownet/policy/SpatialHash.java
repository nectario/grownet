// File: src/java/ai/nektron/grownet/policy/SpatialHash.java
package ai.nektron.grownet.policy;

import java.util.*;
import static java.lang.Math.floor;

public final class SpatialHash<K> {
    private final double cellSize;
    private final Map<List<Integer>, List<K>> cells = new HashMap<>();

    public SpatialHash(double cellSize) { this.cellSize = cellSize; }

    private List<Integer> keyForPosition(double[] pos) {
        int kx = (int) floor(pos[0] / cellSize);
        int ky = (int) floor(pos[1] / cellSize);
        int kz = (int) floor(pos[2] / cellSize);
        return Arrays.asList(kx, ky, kz);
    }

    public void insert(K item, double[] pos) {
        List<Integer> key = keyForPosition(pos);
        cells.computeIfAbsent(key, kk -> new ArrayList<>()).add(item);
    }

    public Iterable<K> near(double[] pos) {
        List<Integer> base = keyForPosition(pos);
        List<K> result = new ArrayList<>();
        for (int offsetZ = -1; offsetZ <= 1; offsetZ++) {
            for (int offsetY = -1; offsetY <= 1; offsetY++) {
                for (int offsetX = -1; offsetX <= 1; offsetX++) {
                    List<Integer> key = Arrays.asList(base.get(0)+offsetX, base.get(1)+offsetY, base.get(2)+offsetZ);
                    List<K> bucket = cells.get(key);
                    if (bucket != null) result.addAll(bucket);
                }
            }
        }
        return result;
    }
}
