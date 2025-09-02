package ai.nektron.grownet;

/**
 * Synaptic weight (per-slot) with adaptive threshold state.
 * Encapsulates local learning, adaptive firing threshold, and simple stats.
 */
public final class Weight {

    // -------- learning parameters & state --------

    /** Base learning step (scaled by neuromodulation on reinforce). */
    private double stepValue = 0.001;

    /** Synaptic efficacy in [-1, +1]. */
    private double strengthValue = 0.0;

    /** Times this weight has been reinforced (saturates). */
    private int reinforcementCount = 0;

    // -------- adaptive threshold state (T0 + EMA-driven drift) --------

    /** Current threshold used for firing decision. */
    private double thresholdValue = 0.0;

    /** Exponential moving average of recent firing events (0..1). */
    private double emaRate = 0.0;

    /** Whether we have imprinted the first-seen threshold. */
    private boolean firstSeen = false;

    // --- Frozen-slot support (opt-in) ---
    private boolean frozen = false;

    public void freeze()   { this.frozen = true; }
    public void unfreeze() { this.frozen = false; }
    public boolean isFrozen() { return frozen; }

    // -------- constants (tune later if needed) --------

    public static final int    HIT_SATURATION = 10_000;
    private static final double EPS   = 0.02;   // first-imprint margin
    private static final double BETA  = 0.01;   // EMA smoothing for firing rate
    private static final double ETA   = 0.02;   // threshold drift step
    private static final double RSTAR = 0.05;   // target firing rate

    // -------- constructors --------

    public Weight() { }

    public Weight(double stepValue) {
        this.stepValue = stepValue;
    }

    // -------- learning --------

    /** Locally reinforce the weight (scaled by neuromodulation factor). */
    public void reinforce(double modulationFactor) {
        if (frozen) return;
        if (reinforcementCount >= HIT_SATURATION) return;

        final double effectiveStep = stepValue * modulationFactor;
        strengthValue = smoothClamp(strengthValue + effectiveStep, -1.0, 1.0);
        reinforcementCount++;
    }

    /**
     * Update the adaptive threshold with the current input, and
     * return whether the weight "fires" under that threshold.
     */
    public boolean updateThreshold(double inputValue) {
        if (frozen) {
            final double inputMagnitude = inputValue;
            return (Math.abs(inputMagnitude) > thresholdValue) || (strengthValue > thresholdValue);
        }
        // First-seen imprint (one-time)
        if (!firstSeen) {
            thresholdValue = Math.abs(inputValue) * (1.0 + EPS);
            firstSeen = true;
        }

        final boolean fired = strengthValue > thresholdValue;
        final double firedIndicator = fired ? 1.0 : 0.0;

        // EMA of recent firing; then drift threshold toward target rate
        emaRate = (1.0 - BETA) * emaRate + BETA * firedIndicator;
        thresholdValue = thresholdValue + ETA * (emaRate - RSTAR);

        return fired;
    }

    // -------- utils --------

    private static double smoothClamp(double input, double lowBound, double highBound) {
        return Math.max(lowBound, Math.min(highBound, input));
    }

    // -------- accessors (read-mostly) --------

    public double getStrengthValue()     { return strengthValue; }
    public double getThresholdValue()    { return thresholdValue; }
    public double getEmaRate()           { return emaRate; }
    public double getStepValue()         { return stepValue; }
    public int    getReinforcementCount(){ return reinforcementCount; }
    public boolean hasSeenFirst()        { return firstSeen; }

    /** Optional: allow experiments to tweak the base learning step. */
    public void setStepValue(double stepValue) {
        this.stepValue = stepValue;
    }
}
