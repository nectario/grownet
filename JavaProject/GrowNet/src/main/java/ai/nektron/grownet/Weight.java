package ai.nektron.grownet;

import static ai.nektron.grownet.MathUtils.smoothClamp;

/** One slot (independent threshold sub‑unit) with local learning. */
public final class Weight {
    public static final int HIT_SATURATION = 10_000;
    public static final double EPS = 0.02;        // T0 slack
    public static final double BETA = 0.01;       // EMA horizon
    public static final double ETA = 0.02;        // homeostatic speed
    public static final double R_TARGET = 0.05;   // desired firing rate

    private double stepValue = 0.001;
    private double strengthValue = 0.0;
    private int hitCount = 0;

    // T0 + T2 adaptive threshold state
    private double thresholdValue = 0.0;
    private double emaRate = 0.0;
    private boolean seenFirst = false;

    public double getStrengthValue() { return strengthValue; }
    public double getThresholdValue() { return thresholdValue; }
    public int getHitCount() { return hitCount; }

    public void setStepValue(double v) { this.stepValue = v; }

    /** Non-linear, ceiling-bounded reinforcement with optional modulation & inhibition. */
    public void reinforce(double modulationFactor, double inhibitionFactor) {
        if (hitCount >= HIT_SATURATION) return;
        double effective = stepValue * modulationFactor;
        strengthValue = smoothClamp(strengthValue + effective, -1.0, 1.0);
        if (inhibitionFactor < 1.0) strengthValue *= inhibitionFactor;
        hitCount++;
    }

    /** T0 imprint + T2 homeostasis. @return true if this slot fires. */
    public boolean updateThreshold(double inputValue) {
        if (!seenFirst) {
            thresholdValue = Math.abs(inputValue) * (1.0 + EPS);
            seenFirst = true;
        }
        boolean fired = strengthValue > thresholdValue;
        emaRate = (1.0 - BETA) * emaRate + BETA * (fired ? 1.0 : 0.0);
        thresholdValue += ETA * (emaRate - R_TARGET);
        return fired;
    }

    public double emaRate() {
        return emaRate;
    }

}
