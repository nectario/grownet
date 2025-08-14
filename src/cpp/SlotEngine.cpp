#include "SlotEngine.h"
#include "Neuron.h"

namespace grownet {
Weight& selectOrCreateSlot(Neuron& neuron, int id) {
    auto& table = neuron.getSlots();
    auto it = table.find(id);
    if (it == table.end()) {
        it = table.emplace(id, Weight{}).first;
    }
    return it->second;
}
} // namespace grownet
