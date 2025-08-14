#include "SlotEngine.h"
#include "Neuron.h"
#include <cmath>
#include <algorithm>

namespace grownet {

static inline double roundOneDecimal(double x) { return std::round(x * 10.0) / 10.0; }

int SlotEngine::computeBinForPercentDelta(double deltaPercent,
                                          const std::unordered_map<int, Weight>& slots) const {
    switch (config.policy) {
        case SlotPolicy::Fixed: {
            if (deltaPercent <= 0.0) return 0;
            double width = std::max(config.slotWidthPercent, 1e-9);
            return static_cast<int>(std::floor(deltaPercent / width));
        }
        case SlotPolicy::NonUniform: {
            for (int i = 0; i < static_cast<int>(config.nonuniformEdges.size()); ++i) {
                if (deltaPercent <= config.nonuniformEdges[i]) return i;
            }
            return static_cast<int>(config.nonuniformEdges.size());
        }
        case SlotPolicy::Adaptive:
        default: {
            double width = std::max(config.slotWidthPercent, 1e-9);
            int candidate = static_cast<int>(std::floor(deltaPercent / width));
            while (slots.find(candidate) != slots.end()) candidate++;
            return candidate;
        }
    }
}

Weight& SlotEngine::selectOrCreateSlot(Neuron& neuron, double inputValue) const {
    auto& slots = neuron.getSlots();
    int binId = 0;

    if (neuron.hasLastInput() && std::abs(neuron.getLastInputValue()) > 1e-12) {
        double deltaPercent = std::abs(inputValue - neuron.getLastInputValue())
                            / std::abs(neuron.getLastInputValue()) * 100.0;
        binId = computeBinForPercentDelta(roundOneDecimal(deltaPercent), slots);
    }

    auto it = slots.find(binId);
    if (it != slots.end()) return it->second;

    if (config.maxSlots.has_value() && static_cast<int>(slots.size()) >= config.maxSlots.value()) {
        return slots.begin()->second; // simple reuse policy
    }

    Weight w; // default
    auto [pos, ok] = slots.emplace(binId, w);
    return pos->second;
}

} // namespace grownet
