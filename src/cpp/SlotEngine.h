#pragma once
#include <cmath>
#include "SlotConfig.h"
#include "Weight.h"

namespace grownet {

class Neuron;

class SlotEngine {
public:
    explicit SlotEngine(const SlotConfig& c) : cfg(c) {}

    int slotId(double lastInput, double currentInput, int /*knownSlots*/) const {
        // for now: percent delta bucketing
        double denom = std::max(1e-9, std::abs(lastInput));
        double deltaPercent = std::abs(currentInput - lastInput) / denom * 100.0;
        switch (cfg.policy) {
            case SlotPolicy::FIXED: {
                double width = std::max(1e-9, cfg.slotWidthPercent);
                return static_cast<int>(deltaPercent / width);
            }
            case SlotPolicy::NONUNIFORM: {
                int idx = 0;
                while (idx < static_cast<int>(cfg.nonuniformEdges.size()) &&
                       deltaPercent > cfg.nonuniformEdges[idx]) idx++;
                return idx;
            }
            case SlotPolicy::ADAPTIVE: {
                double width = std::max(1e-9, cfg.slotWidthPercent);
                return static_cast<int>(deltaPercent / width);
            }
        }
        return 0;
    }

private:
    SlotConfig cfg;
};

Weight& selectOrCreateSlot(Neuron& neuron, int slotId);

} // namespace grownet
