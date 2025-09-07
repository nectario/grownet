// File: src/java/ai/nektron/grownet/policy/DeterministicLayout.java
package ai.nektron.grownet.policy;

public final class DeterministicLayout {
    public static final double LAYER_SPACING = 4.0;
    public static final double GRID_SPACING  = 1.2;

    public static double[] position(String regionName, int layerIndex, int neuronIndex, int layerHeight, int layerWidth) {
        if (layerHeight > 0 && layerWidth > 0) {
            int rowIndex = neuronIndex / layerWidth;
            int colIndex = neuronIndex % layerWidth;
            double xCoord = (colIndex - (layerWidth - 1) / 2.0) * GRID_SPACING;
            double yCoord = ((layerHeight - 1) / 2.0 - rowIndex) * GRID_SPACING;
            double zCoord = ((double) layerIndex) * LAYER_SPACING;
            return new double[]{xCoord, yCoord, zCoord};
        }
        // Fallback grid (ceil-sqrt layout)
        int gridSide = (int) Math.sqrt(neuronIndex + 1);
        if (gridSide * gridSide < neuronIndex + 1) gridSide += 1;
        int rowIndex = neuronIndex / gridSide;
        int colIndex = neuronIndex % gridSide;
        double xCoord = (colIndex - (gridSide - 1) / 2.0) * GRID_SPACING;
        double yCoord = ((gridSide - 1) / 2.0 - rowIndex) * GRID_SPACING;
        double zCoord = ((double) layerIndex) * LAYER_SPACING;
        return new double[]{xCoord, yCoord, zCoord};
    }
}
