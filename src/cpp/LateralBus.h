
#pragma once
#include <algorithm>
#include <cstdint>

namespace grownet {

class LateralBus {
public:
    LateralBus() = default;

    void setInhibitionFactor(double factor) { inhibitionFactor = std::clamp(factor, 0.0, 1.0); }
    void setModulationFactor(double factor) { modulationFactor = factor; }

    double getInhibitionFactor() const { return inhibitionFactor; }
    double getModulationFactor() const { return modulationFactor; }

    void setInhibitionDecay(double decay) { inhibitionDecay = std::clamp(decay, 0.0, 1.0); }
    void setModulationRelax(double relax) { modulationRelax = std::clamp(relax, 0.0, 1.0); }

    void decay() {
        // advance one step and apply simple decay/relaxation
        ++currentStep;
        inhibitionFactor *= inhibitionDecay;
        // drive modulation back towards 1.0
        modulationFactor = 1.0 + (modulationFactor - 1.0) * modulationRelax;
    }

    std::int64_t getCurrentStep() const { return currentStep; }

private:
    double inhibitionFactor {0.0}; // 0..1 (multiplicative damping)
    double modulationFactor {1.0}; // scales learning step
    double inhibitionDecay  {0.90};
    double modulationRelax  {0.90};
    std::int64_t currentStep {0};
};

} // namespace grownet
