package ai.nektron.grownet.policy;

public final class DeterministicLayout {
    public static final double LAYER_SPACING = 4.0;
    public static final double GRID_SPACING  = 1.2;

    public static double[] position(String regionName, int layerIndex, int neuronIndex, int layerHeight, int layerWidth) {
        if (layerHeight > 0 && layerWidth > 0) {
            int rowIndex = neuronIndex / layerWidth;
            int colIndex = neuronIndex % layerWidth;
            double offsetX = (colIndex - (layerWidth - 1) / 2.0) * GRID_SPACING;
            double offsetY = ((layerHeight - 1) / 2.0 - rowIndex) * GRID_SPACING;
            double offsetZ = layerIndex * LAYER_SPACING;
            return new double[] { offsetX, offsetY, offsetZ };
        }
        int plusOne = neuronIndex + 1;
        int gridSide = (int) Math.sqrt(plusOne);
        if (gridSide * gridSide < plusOne) gridSide++;
        int rowIndex2 = neuronIndex / gridSide;
        int colIndex2 = neuronIndex % gridSide;
        double offsetX2 = (colIndex2 - (gridSide - 1) / 2.0) * GRID_SPACING;
        double offsetY2 = ((gridSide - 1) / 2.0 - rowIndex2) * GRID_SPACING;
        double offsetZ2 = layerIndex * LAYER_SPACING;
        return new double[] { offsetX2, offsetY2, offsetZ2 };
    }
}

