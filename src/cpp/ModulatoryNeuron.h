#pragma once
#include "Neuron.h"
#include "LateralBus.h"
#include "SlotConfig.h"

namespace grownet {

// Modulatory neuron: emits a modulation pulse that scales learning.
class ModulatoryNeuron final : public Neuron {
public:
    ModulatoryNeuron(const std::string& id,
                     LateralBus&        sharedBus,
                     const SlotConfig&  slotCfg,
                     int                slotLimit = -1)
    : Neuron(id, sharedBus, slotCfg, slotLimit) {}

    // Unified contract: subclasses react to successful spike via onOutput(amplitude).
    // (Older code used a `fire(double)` method—this replaces it.)
    void onOutput(double amplitude) override {
        // Interpret amplitude as the instantaneous modulation multiplier.
        bus->setModulationFactor(amplitude);
    }
};

} // namespace grownet