package ai.nektron.grownet;

public final class RegionBus {
    private double inhibitionFactor = 1.0;  // 1.0 = no inhibition
    private double modulationFactor = 1.0;  // scales learning rate
    private long currentStep = 0L;

    public double getInhibitionFactor() { return inhibitionFactor; }
    public double getModulationFactor() { return modulationFactor; }
    public long getCurrentStep()       { return currentStep; }

    public void setInhibitionFactor(double value) { inhibitionFactor = value; }
    public void setModulationFactor(double value) { modulationFactor = value; }

    /** Advance one tick and reset one‑tick pulses. */
    public void decay() {
        inhibitionFactor = 1.0;
        modulationFactor = 1.0;
        currentStep += 1;
    }
}
