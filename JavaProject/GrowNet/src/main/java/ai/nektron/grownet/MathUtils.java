package ai.nektron.grownet;

final class MathUtils {
    private MathUtils() {}

    static double smoothStep(double edgeStart, double edgeEnd, double value) {
        if (edgeEnd == edgeStart) return 0.0;
        double t = (value - edgeStart) / (edgeEnd - edgeStart);
        if (t < 0.0) t = 0.0;
        else if (t > 1.0) t = 1.0;
        return t * t * (3.0 - 2.0 * t);
    }

    static double smoothClamp(double value, double lower, double upper) {
        return smoothStep(0.0, 1.0, (value - lower) / (upper - lower)) * (upper - lower) + lower;
    }
}
