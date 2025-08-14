#pragma once
#include "Neuron.h"

namespace grownet {

class OutputNeuron : public Neuron {
public:
    OutputNeuron(const std::string& name, LateralBus& bus, double smoothing)
        : Neuron(name, bus, SlotConfig::singleSlot(), 1), smoothing(smoothing) {
        // Ensure slot zero exists
        auto& m = getSlots();
        if (m.find(0) == m.end()) m.emplace(0, Weight{});
    }

    bool onInput(double value) override {
        Weight& slot = getSlots()[0];
        slot.reinforce(getBus().getModulationFactor());
        bool fired = slot.updateThreshold(value);
        if (fired) onOutput(value);
        return fired;
    }

    void onOutput(double amplitude) override { lastEmitted = amplitude; }
    void endTick() override { lastEmitted *= (1.0 - smoothing); } // simple decay
    double getOutputValue() const { return lastEmitted; }

private:
    double smoothing {0.2};
    double lastEmitted {0.0};
};

} // namespace grownet