#pragma once
#include "Neuron.h"

namespace grownet {
class InhibitoryNeuron : public Neuron {
public:
    InhibitoryNeuron(std::string id, LateralBus& bus, const SlotConfig& cfg, int limit = -1)
        : Neuron(std::move(id), bus, cfg, limit) {}

    void onOutput(double amplitude) override {
        (void)amplitude;
        getBus().setInhibitionFactor(0.7); // simple pulse
        notifyFire(amplitude);
        // no downstream propagation
    }
};
} // namespace grownet
