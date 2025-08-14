#pragma once
#include "Neuron.h"
#include "LateralBus.h"
#include "SlotConfig.h"

namespace grownet {

// Inhibitory neuron: emits an inhibition pulse on the shared bus when it fires.
class InhibitoryNeuron final : public Neuron {
public:
    InhibitoryNeuron(const std::string& id,
                     LateralBus&        sharedBus,
                     const SlotConfig&  slotCfg,
                     int                slotLimit = -1)
    : Neuron(id, sharedBus, slotCfg, slotLimit) {}

    // New unified contract: subclasses react to successful spike via onOutput(amplitude).
    // (Older code used a `fire(double)` method—this replaces it.)
    void onOutput(double amplitude) override {
        // Interpret amplitude as the instantaneous inhibition factor [0..1].
        bus->setInhibitionFactor(amplitude);
    }
};

} // namespace grownet