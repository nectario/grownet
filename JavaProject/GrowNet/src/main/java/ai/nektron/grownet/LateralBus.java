package ai.nektron.grownet;

/**
 * Per-layer bus carrying transient inhibitory and modulatory signals.
 * Values decay each tick.
 */
public class LateralBus {
    private long currentStep = 0L;
    private double inhibitionFactor = 1.0;   // multiplicative effect on strengths (<=1)
    private double modulationScale  = 1.0;   // scales learning step
    private double inhibitionDecay  = 0.90;  // decay per tick toward 1.0
    private double modulationDecay  = 0.0;   // resets toward 1.0 quickly

    public long getCurrentStep() { return currentStep; }

    public double getInhibitionFactor() { return inhibitionFactor; }
    public double getModulationScale()  { return modulationScale;  }

    /** Apply an inhibitory pulse (values < 1.0). */
    public void pulseInhibition(double factor) {
        inhibitionFactor = MathUtils.clamp(factor, 0.0, 1.0);
    }

    /** Apply a modulatory pulse (> 0.0). */
    public void pulseModulation(double scale) {
        modulationScale = Math.max(0.0, scale);
    }

    /** Advance one tick; inhibition relaxes to 1.0, modulation relaxes to 1.0. */
    public void decay() {
        currentStep += 1;
        // Relax inhibition upward toward 1.0
        inhibitionFactor = 1.0 - (1.0 - inhibitionFactor) * inhibitionDecay;
        // Relax modulation toward 1.0
        modulationScale = 1.0 + (modulationScale - 1.0) * modulationDecay;
        // Snap very close values to 1.0 to avoid drift
        if (Math.abs(inhibitionFactor - 1.0) < 1e-6) inhibitionFactor = 1.0;
        if (Math.abs(modulationScale  - 1.0) < 1e-6) modulationScale  = 1.0;
    }
}