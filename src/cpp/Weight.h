#pragma once
#include "MathUtils.h"
#include <cmath>

namespace grownet {

    // One slot (independent threshold sub-unit) with local learning.
    class Weight {
    public:
        // Learning constants
        static constexpr int    HIT_SATURATION = 10'000;
        static constexpr double EPS            = 0.02;  // T0 slack
        static constexpr double BETA           = 0.01;  // EMA horizon
        static constexpr double ETA            = 0.02;  // homeostatic speed
        static constexpr double R_TARGET       = 0.05;  // desired firing rate

        Weight() = default;

        // Non-linear, ceiling-bounded reinforcement with optional modulation & inhibition.
        void reinforce(double modulationFactor = 1.0, double inhibitionFactor = 1.0);

        // T0 imprint + T2 homeostasis. Returns true if this slot fires.
        bool updateThreshold(double inputValue);

        // Accessors for logging/introspection
        double getStrengthValue()  const { return strengthValue; }
        double getThresholdValue() const { return thresholdValue; }
        double getEmaRate()        const { return emaRate; }
        int    getHitCount()       const { return hitCount; }

        void   setStepValue(double value) { stepValue = value; }

    private:
        double stepValue      {0.001};
        double strengthValue  {0.0};
        int    hitCount       {0};

        double thresholdValue {0.0};
        double emaRate        {0.0};
        bool   seenFirst      {false};
    };

} // namespace grownet
