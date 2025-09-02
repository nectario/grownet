/* Out-of-line spatial slot selection to avoid Neuron header cycles. */
#include "SlotEngine.h"
#include "Neuron.h"      // needs full Neuron for anchorRow/anchorCol/getSlots
#include <algorithm>
#include <cmath>
#include <limits>
#include <utility>

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

// Keep the math here so the header stays declaration-only.
std::pair<int,int> SlotEngine::slotId2D(int anchorRow, int anchorCol, int row, int col) const {
    const double eps    = std::max(1e-12, cfg.epsilonScale);
    const double denomR = std::max(std::abs(static_cast<double>(anchorRow)), eps);
    const double denomC = std::max(std::abs(static_cast<double>(anchorCol)), eps);
    const double dpr    = std::abs(static_cast<double>(row - anchorRow)) / denomR * 100.0;
    const double dpc    = std::abs(static_cast<double>(col - anchorCol)) / denomC * 100.0;
    const double bwR    = std::max(0.1, cfg.binWidthPct);
    const double bwC    = std::max(0.1, cfg.binWidthPct);
    return { static_cast<int>(std::floor(dpr / bwR)),
             static_cast<int>(std::floor(dpc / bwC)) };
}

Weight& SlotEngine::selectOrCreateSlot2D(Neuron& neuron, int row, int col) const {
    // FIRST-anchor semantics on (row,col)
    if (neuron.anchorRow < 0 || neuron.anchorCol < 0) {
        neuron.anchorRow = row;
        neuron.anchorCol = col;
    }

    auto rowColPair = slotId2D(neuron.anchorRow, neuron.anchorCol, row, col);
    const int limit = (cfg.slotLimit > 0) ? cfg.slotLimit : std::numeric_limits<int>::max();
    const int boundedRow = std::min(rowColPair.first,  limit - 1);
    const int boundedCol = std::min(rowColPair.second, limit - 1);
    const int key = boundedRow * 100000 + boundedCol; // simple packing

    auto& slots = neuron.getSlots();
    auto slotIter = slots.find(key);
    if (slotIter == slots.end()) {
        slotIter = slots.emplace(key, Weight{}).first;
    }
    return slotIter->second;
}

} // namespace grownet
