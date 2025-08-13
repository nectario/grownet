
#pragma once
#include <algorithm>
#include <cmath>

namespace grownet {

class Weight {
public:
    // Hyper-parameters (can be tuned per-experiment)
    static constexpr double epsilonFirst = 1e-3; // small margin on first imprint
    static constexpr double beta         = 0.01; // EMA horizon for firing rate
    static constexpr double eta          = 0.02; // adaptive threshold speed
    static constexpr double rStar        = 0.05; // target firing rate
    static constexpr int    saturationHits = 10000;
    static constexpr double baseStep       = 0.01; // base reinforcement step

    // Accessors
    double getStrengthValue() const { return strength; }
    double getThresholdValue() const { return theta; }
    double getEmaRate() const { return emaRate; }
    int    getHitCount() const { return hitCount; }

    // Learning: reinforcement scaled by (modulation) and damped by (inhibition)
    void reinforce(double modulationFactor, double inhibitionFactor) {
        if (hitCount >= saturationHits) return;
        double effectiveStep = baseStep * modulationFactor;
        // apply simple non-linear clamp
        strength = smoothClamp(strength + effectiveStep * (1.0 - inhibitionFactor), -1.0, 1.0);
        ++hitCount;
    }

    // Threshold update: returns true if "fired"
    bool updateThreshold(double inputValue) {
        if (!seenFirst) {
            theta = std::abs(inputValue) * (1.0 + epsilonFirst);
            seenFirst = true;
        }
        bool fired = strength > theta;
        double firedFloat = fired ? 1.0 : 0.0;
        emaRate = (1.0 - beta) * emaRate + beta * firedFloat;
        theta  += eta * (emaRate - rStar);
        return fired;
    }

private:
    static inline double smoothClamp(double value, double minVal, double maxVal) {
        // tanh-based soft clamp
        double center = 0.5 * (minVal + maxVal);
        double half   = 0.5 * (maxVal - minVal);
        return center + half * std::tanh((value - center) / (half + 1e-9));
    }

    double strength {0.0};
    double theta    {0.0};
    double emaRate  {0.0};
    int    hitCount {0};
    bool   seenFirst {false};
};

} // namespace grownet
