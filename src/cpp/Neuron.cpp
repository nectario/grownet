#include "Neuron.h"
#include <cmath>

namespace grownet {

Neuron::Neuron(std::string id, const SlotConfig& cfg, RegionBus* sharedBus)
: neuronId(std::move(id))
, bus(sharedBus ? *sharedBus : RegionBus{})
, slotEngine(cfg) {}

bool Neuron::onInput(double value) {
    Weight& slot = slotEngine.selectOrCreateSlot(*this, value);

    slot.reinforce(bus.getModulationFactor(), bus.getInhibitionFactor());
    bool fired = slot.updateThreshold(value);

    if (fired) fire(value);

    haveLastInput = true;
    lastInputValue = value;
    return fired;
}

void Neuron::fire(double inputValue) {
    for (auto& syn : outgoing) {
        if (syn.deliver(inputValue)) {
            syn.getTarget().onInput(inputValue);
        }
    }
}

} // namespace grownet
