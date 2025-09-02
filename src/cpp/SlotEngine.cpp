/* Out-of-line spatial slot selection to avoid Neuron header cycles. */
#include "SlotEngine.h"
#include "Neuron.h"
#include <algorithm>
#include <climits>

namespace grownet {

Weight& SlotEngine::selectOrCreateSlot(Neuron& neuron, double inputValue) const {
    // FIRST-anchor logic
    if (!neuron.focusSet && cfg.anchorMode == AnchorMode::FIRST) {
        neuron.focusAnchor = inputValue;
        neuron.focusSet = true;
    }
    const double anchor = neuron.focusAnchor;
    const double denom = std::max(std::abs(anchor), std::max(1e-12, cfg.epsilonScale));
    const double deltaPct = std::abs(inputValue - anchor) / denom * 100.0;
    const double bin = std::max(0.1, cfg.binWidthPct);
    int desiredId = static_cast<int>(std::floor(deltaPct / bin));

    // clamp to slotLimit domain
    if (cfg.slotLimit > 0 && desiredId >= cfg.slotLimit) desiredId = cfg.slotLimit - 1;

    auto& slots = neuron.getSlots();
    auto iter = slots.find(desiredId);
    if (iter == slots.end()) {
        if (cfg.slotLimit > 0 && static_cast<int>(slots.size()) >= cfg.slotLimit) {
            int reuseId = std::min(desiredId, cfg.slotLimit - 1);
            iter = slots.emplace(reuseId, Weight{}).first;
        } else {
            iter = slots.emplace(desiredId, Weight{}).first;
        }
    }
    // record last used slot for convenience freezing
    neuron.setLastSlotId(iter->first);
    return iter->second;
}

Weight& SlotEngine::selectOrCreateSlot2D(Neuron& neuron, int row, int col) const {
    // FIRST-anchor semantics on (row,col)
    if (neuron.anchorRow < 0 || neuron.anchorCol < 0) {
        neuron.anchorRow = row;
        neuron.anchorCol = col;
    }

    auto rc = slotId2D(neuron.anchorRow, neuron.anchorCol, row, col);
    const int limit = (cfg.slotLimit > 0) ? cfg.slotLimit : INT_MAX;
    const int rb = std::min(rc.first,  limit - 1);
    const int cb = std::min(rc.second, limit - 1);
    const int key = rb * 100000 + cb; // simple packing

    auto& slots = neuron.getSlots();
    auto it = slots.find(key);
    if (it == slots.end()) {
        it = slots.emplace(key, Weight{}).first;
    }
    return it->second;
}

} // namespace grownet
