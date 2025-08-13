package ai.nektron.grownet;

/**
 * Slot-level memory and adaptive threshold state.
 * Each Weight lives inside a Neuron's slot map and is used by one Synapse/slot.
 */
public class Weight {
    // Reinforcement state
    private double strength = 0.0;           // [-1, +1]
    private int    hitCount = 0;             // saturates at hitSaturation

    // Adaptive threshold (T0 + T2 hybrid) state
    private boolean seenFirst = false;
    private double  threshold = 0.0;
    private double  emaRate   = 0.0;

    // Hyperparameters (tunable)
    private int    hitSaturation      = 10_000;
    private double learningStep       = 0.02;  // baseline reinforce step
    private double epsilonImprint     = 0.01;  // T0 slack
    private double emaSmoothing       = 0.01;  // beta
    private double adaptSpeed         = 0.02;  // eta
    private double targetRate         = 0.05;  // r*
    private double minThreshold       = 1e-6;

    public double getStrength()  { return strength; }
    public int    getHitCount()  { return hitCount; }
    public double getThreshold() { return threshold; }
    public double getEmaRate()   { return emaRate;  }

    public void setLearningStep(double step) { this.learningStep = step; }
    public void setEmaSmoothing(double value) { this.emaSmoothing = value; }
    public void setAdaptSpeed(double value) { this.adaptSpeed = value; }
    public void setTargetRate(double value) { this.targetRate = value; }
    public void setEpsilonImprint(double value) { this.epsilonImprint = value; }
    public void setHitSaturation(int value) { this.hitSaturation = Math.max(1, value); }

    /** Non-linear reinforcement with neuromodulation and inhibition. */
    public void reinforce(double modulationScale, double inhibitionFactor) {
        if (hitCount >= hitSaturation) return;
        double effectiveStep = learningStep * Math.max(0.0, modulationScale);
        // Inhibition shrinks effective influence without making it negative
        effectiveStep *= MathUtils.clamp(inhibitionFactor, 0.0, 1.0);
        strength = MathUtils.smoothClamp(strength + effectiveStep, -1.0, 1.0);
        hitCount += 1;
    }

    /**
     * T0 + T2 hybrid adaptive threshold update.
     * Returns true if the slot crosses threshold after update (i.e., fires).
     */
    public boolean updateThreshold(double inputValue) {
        if (!seenFirst) {
            threshold = Math.max(Math.abs(inputValue) * (1.0 + epsilonImprint), minThreshold);
            seenFirst = true;
        }
        boolean fired = strength > threshold;
        emaRate = (1.0 - emaSmoothing) * emaRate + emaSmoothing * (fired ? 1.0 : 0.0);
        threshold += adaptSpeed * (emaRate - targetRate);
        threshold = Math.max(threshold, minThreshold);
        return fired;
    }
}