#include "Neuron.h"

namespace grownet {

bool Neuron::onInput(double value) {
    Weight& weight = slotEngine.selectOrCreateSlot(*this, value);
    weight.reinforce(getBus().getModulationFactor());
    bool fired = weight.updateThreshold(value);
    setFiredLast(fired);
    setLastInputValue(value);
    return fired;
}

void Neuron::onOutput(double amplitude) {
    notifyFire(amplitude);
    // Default excitatory fanout: deliver to connected targets
    for (auto& syn : outgoing) {
        if (syn.target) {
            bool downstreamFired = syn.target->onInput(amplitude);
            if (downstreamFired) syn.target->onOutput(amplitude);
        }
    }
}

} // namespace grownet
