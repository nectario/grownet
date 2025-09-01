package ai.nektron.grownet;

/**
 * Lightweight “lateral” event bus shared within a Layer.
 * - inhibitionFactor in [0, 1] (0 = none, 1 = full).
 * - modulationFactor scales learning rate (1.0 = neutral).
 * - currentStep increments once per tick (used for staleness checks).
 */
public class LateralBus {
    private double inhibitionFactor = 0.0;
    private double modulationFactor = 1.0;
    private long   currentStep      = 0L;

    public double getInhibitionFactor() { return inhibitionFactor; }
    public double getModulationFactor() { return modulationFactor; }
    public long   getCurrentStep()      { return currentStep; }

    public void setInhibitionFactor(double value) {
        if (value < 0.0) value = 0.0;
        if (value > 1.0) value = 1.0;
        inhibitionFactor = value;
    }

    public void setModulationFactor(double value) {
        modulationFactor = value;
    }

    /** Called once at the end of each tick by Layer.endTick(). */
    public void decay() {
        inhibitionFactor = 0.0;
        modulationFactor = 1.0;
        currentStep += 1;
    }
}
