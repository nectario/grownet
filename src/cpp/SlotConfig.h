#pragma once
#include <cmath>

namespace grownet {

enum class SlotPolicy { FIXED, NONUNIFORM, ADAPTIVE };
enum class AnchorMode { FIRST, EMA, WINDOW, LAST };

struct SlotConfig {
    // Existing policy knobs
    SlotPolicy policy { SlotPolicy::FIXED };
    double fixedBinPercent { 10.0 }; // when FIXED: %Δ per bin
    int maxSlots { -1 };             // -1 means unlimited

    // Temporal-focus knobs
    AnchorMode anchorMode { AnchorMode::FIRST };
    double binWidthPct { 10.0 };
    double epsilonScale { 1e-6 };
    double recenterThresholdPct { 35.0 };
    int    recenterLockTicks { 20 };
    double anchorBeta { 0.05 };
    double outlierGrowthThresholdPct { 60.0 };
    int    slotLimit { 16 };

    static SlotConfig fixed(double binPercent, int limit = -1) {
        SlotConfig cfg;
        cfg.policy = SlotPolicy::FIXED;
        cfg.fixedBinPercent = binPercent;
        cfg.maxSlots = limit;
        return cfg;
    }
};

} // namespace grownet
