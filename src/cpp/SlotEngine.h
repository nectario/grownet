#pragma once
#include <unordered_map>
#include <cmath>
#include "SlotConfig.h"
#include "Weight.h"

namespace grownet {

class Neuron; // forward decl

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
        // Placeholder: percent deltas per-axis; mirrors scalar approach.
        const double eps = std::max(1e-12, cfg.epsilonScale);
        const double denomR = std::max(std::abs(static_cast<double>(anchorRow)), eps);
        const double denomC = std::max(std::abs(static_cast<double>(anchorCol)), eps);
        const double dpr = std::abs(static_cast<double>(row - anchorRow)) / denomR * 100.0;
        const double dpc = std::abs(static_cast<double>(col - anchorCol)) / denomC * 100.0;
        const double bwR = std::max(0.1, cfg.binWidthPct);
        const double bwC = std::max(0.1, cfg.binWidthPct);
        return { static_cast<int>(std::floor(dpr / bwR)), static_cast<int>(std::floor(dpc / bwC)) };
    }

    inline Weight& selectOrCreateSlot2D(Neuron& neuron, int row, int col) const {
        // Minimal: reuse scalar engine with FIRST anchor semantics on (row,col)
        if (neuron.anchorRow < 0 || neuron.anchorCol < 0) {
            neuron.anchorRow = row; neuron.anchorCol = col;
        }
        auto rc = slotId2D(neuron.anchorRow, neuron.anchorCol, row, col);
        int limit = cfg.slotLimit > 0 ? cfg.slotLimit : 0x7fffffff;
        int rb = std::min(rc.first,  limit - 1);
        int cb = std::min(rc.second, limit - 1);
        int key = rb * 100000 + cb; // simple packing
        auto& slots = neuron.getSlots();
        auto it = slots.find(key);
        if (it == slots.end()) it = slots.emplace(key, Weight{}).first;
        return it->second;
    }
};

} // namespace grownet
