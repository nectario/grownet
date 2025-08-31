#pragma once
#include <algorithm>
#include <cmath>

namespace grownet {
/** Per-slot weight + adaptive threshold state. */
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
    static constexpr int    HIT_SATURATION = 10'000;
    static constexpr double EPS   = 0.02;
    static constexpr double BETA  = 0.01;
    static constexpr double ETA   = 0.02;
    static constexpr double RSTAR = 0.05;

    inline static double smoothClamp(double value, double low, double high) {
        return std::max(low, std::min(high, value));
    }

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
        double isFired = fired ? 1.0 : 0.0;
        emaRate = (1.0 - BETA) * emaRate + BETA * isFired;
        thresholdValue = thresholdValue + ETA * (emaRate - RSTAR);
        return fired;
    }

    // accessors often handy in higher-level code
    double getStrengthValue() const { return strengthValue; }
    void   setStrengthValue(double value) { strengthValue = value; }
    bool   isFirstSeen() const { return firstSeen; }
    void   setFirstSeen(bool first) { firstSeen = first; }
    double getThresholdValue() const { return thresholdValue; }
    void   setThresholdValue(double value) { thresholdValue = value; }
};
} // namespace grownet
