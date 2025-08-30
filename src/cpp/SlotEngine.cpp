#include "SlotEngine.h"
#include "Neuron.h"
#include <algorithm>

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
    return iter->second;
}

} // namespace grownet
