#pragma once
#include <cmath>

namespace grownet {

enum class SlotPolicy { FIXED, NONUNIFORM, ADAPTIVE };

struct SlotConfig {
    SlotPolicy policy { SlotPolicy::FIXED };
    double fixedBinPercent { 10.0 }; // when FIXED: %Δ per bin (e.g., 10 means bins are -10..0..+10)
    int maxSlots { -1 };             // -1 means unlimited
    static SlotConfig fixed(double binPercent, int limit = -1) {
        SlotConfig cfg;
        cfg.policy = SlotPolicy::FIXED;
        cfg.fixedBinPercent = binPercent;
        cfg.maxSlots = limit;
        return cfg;
    }
};

} // namespace grownet
