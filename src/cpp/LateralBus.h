#pragma once

namespace grownet {

    class LateralBus {
    public:
        LateralBus() = default;

        double getInhibitionFactor() const { return inhibitionFactor; }
        double getModulationFactor() const { return modulationFactor; }
        long long getCurrentStep()   const { return currentStep; }

        void setInhibitionFactor(double value) { inhibitionFactor = value; }
        void setModulationFactor(double value) { modulationFactor = value; }

        // Advance one tick; reset transient signals
        void decay() {
            inhibitionFactor = 1.0;
            modulationFactor = 1.0;
            currentStep += 1;
        }

    private:
        double inhibitionFactor {1.0};  // 1.0 = no inhibition
        double modulationFactor {1.0};  // scales learning rate
        long long currentStep   {0};
    };

} // namespace grownet
