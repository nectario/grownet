package ai.nektron.grownet;

/** Shared, per-layer bus for simple, time-local signals. */
public final class LateralBus {
    private double inhibitionFactor = 1.0;  // 1.0 means no inhibition
    private double modulationFactor = 1.0;  // scales learning rate
    private long currentStep = 0L;          // global tick

    public double inhibitionFactor() { return inhibitionFactor; }
    public double modulationFactor() { return modulationFactor; }
    public long currentStep()        { return currentStep; }

    public void setInhibitionFactor(double v) { this.inhibitionFactor = v; }
    public void setModulationFactor(double v) { this.modulationFactor = v; }

    public double getInhibitionFactor() {
        return inhibitionFactor;
    }

    public double getModulationFactor() {
        return modulationFactor;
    }
    public long getCurrentStep() {
        return currentStep;
    }
    public void setCurrentStep(long currentStep) {
        this.currentStep = currentStep;
    }

    /** Advance one tick, resetting transient signals. */
    public void decay() {
        this.inhibitionFactor = 1.0;
        this.modulationFactor = 1.0;
        this.currentStep++;
    }
}
