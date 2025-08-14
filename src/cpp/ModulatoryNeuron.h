#pragma once
#include "Neuron.h"

namespace grownet {
class ModulatoryNeuron : public Neuron {
public:
    ModulatoryNeuron(std::string id, LateralBus& bus, const SlotConfig& cfg, int limit = -1)
        : Neuron(std::move(id), bus, cfg, limit) {}

    void onOutput(double amplitude) override {
        (void)amplitude;
        getBus().setModulationFactor(1.5); // simple pulse
        notifyFire(amplitude);
        // no downstream propagation
    }
};
} // namespace grownet
