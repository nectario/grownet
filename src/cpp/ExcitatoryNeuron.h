#pragma once
#include "Neuron.h"

namespace grownet {
class ExcitatoryNeuron : public Neuron {
public:
    ExcitatoryNeuron(std::string id, LateralBus& bus, const SlotConfig& cfg, int limit = -1)
        : Neuron(std::move(id), bus, cfg, limit) {}
    // inherit onInput/onOutput
};
} // namespace grownet
