package ai.nektron.grownet;

final class Weight {
    // learning
    double stepValue = 0.001;
    double strengthValue = 0.0;
    int    reinforcementCount = 0;

    // adaptive threshold state
    double thresholdValue = 0.0;
    double emaRate = 0.0;
    boolean firstSeen = false;

    // constants (can be made configurable later)
    static final int   HIT_SATURATION = 10_000;
    static final double EPS   = 0.02;
    static final double BETA  = 0.01;
    static final double ETA   = 0.02;
    static final double RSTAR = 0.05;

    void reinforce(double modulationFactor) {
        if (reinforcementCount >= HIT_SATURATION) return;
        double step = stepValue * modulationFactor;
        strengthValue = smoothClamp(strengthValue + step, -1.0, 1.0);
        reinforcementCount++;
    }

    boolean updateThreshold(double inputValue) {
        if (!firstSeen) {
            thresholdValue = Math.abs(inputValue) * (1.0 + EPS);
            firstSeen = true;
        }
        boolean fired = strengthValue > thresholdValue;
        double f = fired ? 1.0 : 0.0;

        emaRate = (1.0 - BETA) * emaRate + BETA * f;
        thresholdValue = thresholdValue + ETA * (emaRate - RSTAR);
        return fired;
    }

    private static double smoothClamp(double x, double lo, double hi) {
        return Math.max(lo, Math.min(hi, x));
    }
}
