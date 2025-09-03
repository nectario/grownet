#pragma once
namespace grownet {
/** Region-wide pulses; currently mirrors LateralBus semantics. */
class RegionBus {
    double inhibitionFactor { 0.0 };
    double modulationFactor { 1.0 };
    long long currentStep   { 0 };
public:
    void setInhibitionFactor(double factor) { inhibitionFactor = factor; }
    void setModulationFactor(double factor) { modulationFactor = factor; }
    double getInhibitionFactor() const { return inhibitionFactor; }
    double getModulationFactor() const { return modulationFactor; }
    void decay() {
        inhibitionFactor *= 0.9;
        modulationFactor  = 1.0;
        ++currentStep;
    }
    long long getCurrentStep() const { return currentStep; }
    long long getStep() const { return currentStep; }
};
} // namespace grownet
