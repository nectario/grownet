#pragma once

namespace grownet {

    class RegionBus {
    public:
        double     getInhibitionFactor() const noexcept { return inhibitionFactor; }
        double     getModulationFactor() const noexcept { return modulationFactor; }
        long long  getCurrentStep()      const noexcept { return currentStep; }

        void setInhibitionFactor(double v) noexcept { inhibitionFactor = v; }
        void setModulationFactor(double v) noexcept { modulationFactor = v; }

        // Advance one tick; reset one‑tick pulses.
        void decay() noexcept {
            inhibitionFactor = 1.0;
            modulationFactor = 1.0;
            ++currentStep;
        }

    private:
        double    inhibitionFactor {1.0};   // 1.0 = no inhibition
        double    modulationFactor {1.0};   // scales learning rate
        long long currentStep      {0};
    };

} // namespace grownet
