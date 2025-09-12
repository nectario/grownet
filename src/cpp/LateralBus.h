#pragma once
namespace grownet {
/** Per-layer lateral bus carrying transient inhibition / neuromodulation. */
class LateralBus {
    double inhibitionFactor { 0.0 };
    double modulationFactor { 1.0 };
    double inhibitionDecay  { 0.90 };  // configurable decay rate (default 0.90)
    long long currentStep   { 0 };     // increments each tick for cooldowns/metrics
public:
    // Setters
    void setInhibitionFactor(double factor) { inhibitionFactor = factor; }
    void setModulationFactor(double factor) { modulationFactor = factor; }
    void setInhibitionDecay(double decay)   { inhibitionDecay = decay; }

    // Getters
    double getInhibitionFactor() const { return inhibitionFactor; }
    double getModulationFactor() const { return modulationFactor; }
    double getInhibitionDecay()  const { return inhibitionDecay; }

    void decay() {
        // Multiplicative inhibition decay; modulation resets; step++
        inhibitionFactor *= inhibitionDecay;
        modulationFactor  = 1.0;
        ++currentStep;
    }
    long long getCurrentStep() const { return currentStep; }
    long long getStep() const { return currentStep; } // compat alias
};
} // namespace grownet
