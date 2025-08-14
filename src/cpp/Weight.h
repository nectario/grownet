#pragma once
#include <algorithm>
#include "MathUtils.h"

namespace grownet {

struct Weight {
    // learning
    double stepValue { 0.001 };
    double strengthValue { 0.0 };
    int    reinforcementCount { 0 };

    // adaptive threshold state
    double thresholdValue { 0.0 };
    double emaRate { 0.0 };
    bool   firstSeen { false };

    // constants
    static constexpr int HIT_SATURATION = 10000;
    static constexpr double EPS  = 0.02;
    static constexpr double BETA = 0.01;
    static constexpr double ETA  = 0.02;
    static constexpr double RSTAR= 0.05;

    void reinforce(double modulationFactor) {
        if (reinforcementCount >= HIT_SATURATION) return;
        double step = stepValue * modulationFactor;
        strengthValue = smoothClamp(strengthValue + step, -1.0, 1.0);
        reinforcementCount++;
    }

    bool updateThreshold(double inputValue) {
        if (!firstSeen) {
            thresholdValue = std::abs(inputValue) * (1.0 + EPS);
            firstSeen = true;
        }
        bool fired = strengthValue > thresholdValue;
        double f = fired ? 1.0 : 0.0;
        emaRate = (1.0 - BETA) * emaRate + BETA * f;
        thresholdValue = thresholdValue + ETA * (emaRate - RSTAR);
        return fired;
    }

    double getStrengthValue() const { return strengthValue; }
    double getThresholdValue() const { return thresholdValue; }
    double getEmaRate() const { return emaRate; }
};

} // namespace grownet
