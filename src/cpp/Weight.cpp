#include "Weight.h"

namespace grownet {

    void Weight::reinforce(double modulationFactor, double inhibitionFactor) {
        if (hitCount >= HIT_SATURATION) return;
        const double effectiveStep = stepValue * modulationFactor;
        strengthValue = smoothClamp(strengthValue + effectiveStep, -1.0, 1.0);
        if (inhibitionFactor < 1.0) {
            strengthValue *= inhibitionFactor;
        }
        hitCount += 1;
    }

    bool Weight::updateThreshold(double inputValue) {
        if (!seenFirst) {
            thresholdValue = std::abs(inputValue) * (1.0 + EPS);
            seenFirst = true;
        }
        const bool fired = (strengthValue > thresholdValue);
        const double firedFloat = fired ? 1.0 : 0.0;
        emaRate = (1.0 - BETA) * emaRate + BETA * firedFloat;
        thresholdValue += ETA * (emaRate - R_TARGET);
        return fired;
    }

} // namespace grownet
