#pragma once
#include <utility>
#include <cmath>
#include "Weight.h"
#include "SlotConfig.h"

namespace grownet {

class Neuron; // forward decl (avoid pulling Neuron.h into this header)

class SlotEngine {
    SlotConfig cfg;
public:
    explicit SlotEngine(const SlotConfig& c) : cfg(c) {}

    // Pick slot ID based on percent delta.
    int slotId(double lastInput, double currentInput, int knownSlots) const {
        (void)knownSlots;
        switch (cfg.policy) {
            case SlotPolicy::FIXED: {
                if (std::abs(lastInput) < 1e-12) return 0;
                double deltaPercent = std::abs(currentInput - lastInput) / std::abs(lastInput) * 100.0;
                int bin = static_cast<int>(std::floor(deltaPercent / cfg.fixedBinPercent));
                return bin;
            }
            case SlotPolicy::NONUNIFORM: {
                // placeholder: same as fixed for now
                if (std::abs(lastInput) < 1e-12) return 0;
                double deltaPercent = std::abs(currentInput - lastInput) / std::abs(lastInput) * 100.0;
                int bin = static_cast<int>(std::floor(deltaPercent / cfg.fixedBinPercent));
                return bin;
            }
            case SlotPolicy::ADAPTIVE: {
                // placeholder: single slot grows as needed
                return 0;
            }
        }
        return 0;
    }

    // Ensure slot exists and return it.
    Weight& selectOrCreateSlot(Neuron& neuron, double inputValue) const;

    // ---- Spatial stubs (Phase B) ----
    inline std::pair<int,int> slotId2D(int anchorRow, int anchorCol, int row, int col) const {
        const double eps   = std::max(1e-12, cfg.epsilonScale);
        const double denomR = std::max(std::abs(static_cast<double>(anchorRow)), eps);
        const double denomC = std::max(std::abs(static_cast<double>(anchorCol)), eps);
        const double dpr = std::abs(static_cast<double>(row - anchorRow)) * 100.0 / denomR;
        const double dpc = std::abs(static_cast<double>(col - anchorCol)) * 100.0 / denomC;
        const double bwR = std::max(0.1, cfg.binWidthPct);
        const double bwC = std::max(0.1, cfg.binWidthPct);
        return { static_cast<int>(std::floor(dpr / bwR)),
                 static_cast<int>(std::floor(dpc / bwC)) };
    }

    // Implemented in SlotEngine.cpp (requires the full Neuron definition)
    Weight& selectOrCreateSlot2D(Neuron& neuron, int row, int col) const;
};

} // namespace grownet
