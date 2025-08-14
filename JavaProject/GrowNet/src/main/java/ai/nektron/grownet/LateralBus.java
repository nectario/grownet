package ai.nektron.grownet;

public class LateralBus {
    private double inhibitionFactor = 0.0; // 0..1
    private double modulationFactor = 1.0; // scales learning rate

    public double inhibitionFactor() { return inhibitionFactor; }
    public double modulationFactor() { return modulationFactor; }

    public void setInhibition(double factor) { inhibitionFactor = factor; }
    public void setModulation(double factor) { modulationFactor = factor; }

    public void decay() {
        inhibitionFactor = 0.0;
        modulationFactor = 1.0;
    }
}
