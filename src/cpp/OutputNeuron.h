#pragma once
#include "Neuron.h"

namespace grownet {
/** Output neuron: captures last emitted amplitude; no downstream propagation. */
class OutputNeuron : public Neuron {
    double lastEmitted { 0.0 };
    double smoothing { 0.0 };
public:
    OutputNeuron(std::string id, LateralBus& bus, const SlotConfig& cfg, double smoothing, int limit = -1)
        : Neuron(std::move(id), bus, cfg, limit), smoothing(smoothing) {
        slots[0]; // ensure slot-0 exists
    }

    bool onInput(double value) override {
        Weight& slot = slots[0];
        slot.reinforce(getBus().getModulationFactor());
        bool fired = slot.updateThreshold(value);
        setFiredLast(fired);
        setLastInputValue(value);
        return fired;
    }

    void onOutput(double amplitude) override {
        lastEmitted = amplitude;
        notifyFire(amplitude);
        // swallow propagation
    }

    void endTick() override { lastEmitted *= (1.0 - smoothing); }

    double getOutputValue() const { return lastEmitted; }
};
} // namespace grownet
