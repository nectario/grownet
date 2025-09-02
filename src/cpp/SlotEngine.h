#pragma once
#include "Weight.h"
#include "SlotConfig.h"

// Forward-declare std::pair to avoid pulling in <utility>
namespace std { template <class T, class U> struct pair; }

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

    // ---- Spatial helpers (Phase B) ----
    // Safe to keep inline (no Neuron access)
    inline std::pair<int,int> slotId2D(int anchorRow, int anchorCol, int row, int col) const;

    // Must touch Neuron → declare only here; define in SlotEngine.cpp
    Weight& selectOrCreateSlot2D(Neuron& neuron, int row, int col) const;
};

} // namespace grownet
