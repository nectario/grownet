#pragma once
#include "Neuron.h"

namespace grownet {

class InputNeuron : public Neuron {
public:
    InputNeuron(const std::string& name, LateralBus& bus, double gain, double epsilonFire)
        : Neuron(name, bus, SlotConfig::singleSlot(), 1), gain(gain), epsilonFire(epsilonFire) {
        // Ensure slot zero exists for the input neuron policy.
        auto& m = getSlots();
        if (m.find(0) == m.end()) m.emplace(0, Weight{});
    }

    bool onInput(double value) override {
        double amplified = gain * value;
        Weight& slot = getSlots()[0];
        slot.reinforce(getBus().getModulationFactor());
        bool fired = slot.updateThreshold(amplified);
        if (fired) onOutput(amplified);
        // keep contract
        return fired;
    }

    void onOutput(double amplitude) override { outputValue = amplitude; }
    double getOutputValue() const { return outputValue; }

private:
    double gain {1.0};
    double epsilonFire {0.01};
    double outputValue {0.0};
};

} // namespace grownet