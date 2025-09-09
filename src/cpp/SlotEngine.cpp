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
    const int lastSid = neuron.getLastSlotId();
    // One-shot reuse after unfreeze
    if (neuron.getPreferLastSlotOnce() && lastSid >= 0) {
        auto& slotsReuse = neuron.getSlots();
        auto iterReuse = slotsReuse.find(lastSid);
        if (iterReuse != slotsReuse.end()) {
            neuron.setPreferLastSlotOnce(false);
            neuron.setLastSlotUsedFallback(false);
            return iterReuse->second;
        }
        // if last id not present, fall through to normal selection
        neuron.setPreferLastSlotOnce(false);
    }

    const double anchor = neuron.focusAnchor;
    const double denom = std::max(std::abs(anchor), std::max(1e-12, cfg.epsilonScale));
    const double deltaPct = std::abs(inputValue - anchor) / denom * 100.0;
    const double bin = std::max(0.1, cfg.binWidthPct);
    const int sidDesired = static_cast<int>(std::floor(deltaPct / bin));

    const int limit = (neuron.getSlotLimit() >= 0 ? neuron.getSlotLimit() : cfg.slotLimit);
    auto& slots = neuron.getSlots();
    const bool atCapacity = (limit > 0 && static_cast<int>(slots.size()) >= limit);
    const bool outOfDomain = (limit > 0 && sidDesired >= limit);
    const bool wantNew = (slots.find(sidDesired) == slots.end());
    const bool useFallback = outOfDomain || (atCapacity && wantNew);

    int sid = useFallback && limit > 0 ? (limit - 1) : sidDesired;
    auto iter = slots.find(sid);
    if (iter == slots.end()) {
        if (atCapacity) {
            if (slots.empty()) {
                iter = slots.emplace(sid, Weight{}).first;
            } else {
                // reuse some existing slot deterministically (first key)
                iter = slots.begin();
            }
        } else {
            iter = slots.emplace(sid, Weight{}).first;
        }
    }
    neuron.setLastSlotId(iter->first);
    neuron.setLastSlotUsedFallback(useFallback);
    if (useFallback) {
        neuron.setLastMissingSlotId(sidDesired);
        neuron.setLastMaxAxisDeltaPct(deltaPct);
    } else {
        neuron.setFallbackStreak(0);
        neuron.setPrevMissingSlotId(-1);
        neuron.setLastMissingSlotId(-1);
    }
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
    const int lastSid = neuron.getLastSlotId();
    if (neuron.getPreferLastSlotOnce() && lastSid >= 0) {
        auto& slotsReuse = neuron.getSlots();
        auto itReuse = slotsReuse.find(lastSid);
        if (itReuse != slotsReuse.end()) {
            neuron.setPreferLastSlotOnce(false);
            neuron.setLastSlotUsedFallback(false);
            return itReuse->second;
        }
        neuron.setPreferLastSlotOnce(false);
    }

    auto rowColPair = slotId2D(neuron.anchorRow, neuron.anchorCol, row, col);
    int rBin = rowColPair.first;
    int cBin = rowColPair.second;
    const double rowDeltaPct = std::abs(row - neuron.anchorRow) / std::max(std::abs(static_cast<double>(neuron.anchorRow)), cfg.epsilonScale) * 100.0;
    const double colDeltaPct = std::abs(col - neuron.anchorCol) / std::max(std::abs(static_cast<double>(neuron.anchorCol)), cfg.epsilonScale) * 100.0;
    const int limit = (neuron.getSlotLimit() >= 0 ? neuron.getSlotLimit() : cfg.slotLimit);
    auto& slots = neuron.getSlots();
    const bool atCapacity = (limit > 0 && static_cast<int>(slots.size()) >= limit);
    const bool outOfDomain = (limit > 0 && (rBin >= limit || cBin >= limit));
    const int desiredKey = rBin * 100000 + cBin;
    const bool wantNew = (slots.find(desiredKey) == slots.end());
    const bool useFallback = outOfDomain || (atCapacity && wantNew);

    int key;
    if (useFallback && limit > 0) {
        key = (limit - 1) * 100000 + (limit - 1);
    } else {
        key = desiredKey;
    }
    auto it = slots.find(key);
    if (it == slots.end()) {
        if (atCapacity) {
            if (slots.empty()) {
                it = slots.emplace(key, Weight{}).first;
            } else {
                it = slots.begin();
            }
        } else {
            it = slots.emplace(key, Weight{}).first;
        }
    }
    neuron.setLastSlotUsedFallback(useFallback);
    neuron.setLastSlotId(it->first);
    if (useFallback) {
        neuron.setLastMissingSlotId(desiredKey);
        neuron.setLastMaxAxisDeltaPct(std::max(rowDeltaPct, colDeltaPct));
    } else {
        neuron.setFallbackStreak(0);
        neuron.setPrevMissingSlotId(-1);
        neuron.setLastMissingSlotId(-1);
    }
    return it->second;
}

} // namespace grownet
