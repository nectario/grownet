#pragma once
#include "Neuron.h"

namespace grownet {
/** Pixel-driven neuron: slot-0 mirrors the input value (with imprint on first tick). */
class InputNeuron : public Neuron {
    double gain { 1.0 };
    double epsilonFire { 0.01 };
public:
    InputNeuron(std::string id, LateralBus& bus, const SlotConfig& cfg, double gain, double eps, int limit = -1)
        : Neuron(std::move(id), bus, cfg, limit), gain(gain), epsilonFire(eps) {
        slots[0]; // ensure slot-0 exists
    }

    bool onInput(double value) override {
        double effective = value * gain;
        Weight& slot = slots[0];
        if (!slot.isFirstSeen()) {
            slot.setThresholdValue(std::max(0.0, effective * (1.0 - epsilonFire)));
            slot.setFirstSeen(true);
        }
        slot.setStrengthValue(effective);
        bool fired = slot.updateThreshold(effective);
        setFiredLast(fired);
        setLastInputValue(effective);
        if (fired) onOutput(effective);
        return fired;
    }
};
} // namespace grownet
