package ai.nektron.grownet;

/** Utility math helpers for GrowNet. */
public final class MathUtils {
    private MathUtils() {}

    /** Smoothly clamps a value into [min, max] using a soft transition near the bounds. */
    public static double smoothClamp(double value, double minValue, double maxValue) {
        if (value < minValue) {
            double distance = minValue - value;
            return minValue - distance / (1.0 + distance);
        }
        if (value > maxValue) {
            double distance = value - maxValue;
            return maxValue + distance / (1.0 + distance * distance);
        }
        return value;
    }

    /** Linear clamp helper. */
    public static double clamp(double value, double minValue, double maxValue) {
        return Math.max(minValue, Math.min(maxValue, value));
    }
}