#include "SlotEngine.h"
#include "Neuron.h"

namespace grownet {

Weight& SlotEngine::selectOrCreateSlot(Neuron& neuron, double inputValue) const {
    int desiredId = 0;
    if (neuron.hasLastInput()) {
        desiredId = slotId(neuron.getLastInputValue(), inputValue, static_cast<int>(neuron.getSlots().size()));
    }
    auto& slots = neuron.getSlots();
    auto iter = slots.find(desiredId);
    if (iter == slots.end()) {
        iter = slots.emplace(desiredId, Weight{}).first;
    }
    return iter->second;
}

} // namespace grownet
