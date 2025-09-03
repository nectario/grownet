#pragma once
namespace grownet {
/** Per-layer lateral bus carrying transient inhibition / neuromodulation. */
class LateralBus {
    double inhibitionFactor { 0.0 };
    double modulationFactor { 1.0 };
    long long currentStep    { 0 };  // increments each tick for cooldowns/metrics
public:
    void setInhibitionFactor(double factor) { inhibitionFactor = factor; }
    void setModulationFactor(double factor) { modulationFactor = factor; }
    double getInhibitionFactor() const { return inhibitionFactor; }
    double getModulationFactor() const { return modulationFactor; }
    void decay() {
        // Simple decay toward neutral values.
        inhibitionFactor *= 0.9;   // decays to 0
        modulationFactor  = 1.0;   // resets to neutral each tick
        ++currentStep;
    }
    long long getCurrentStep() const { return currentStep; }
    long long getStep() const { return currentStep; } // compat alias
};
} // namespace grownet
