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

    // -------- Growth knobs (parity with Python/Java) --------
    bool growthEnabled { true };
    bool neuronGrowthEnabled { true };
    bool layerGrowthEnabled { false }; // reserved for future region policy in C++
    int  fallbackGrowthThreshold { 3 }; // consecutive fallback uses before growth
    int  neuronGrowthCooldownTicks { 0 }; // ticks between neuron growth events

    static SlotConfig fixed(double binPercent, int limit = -1) {
        SlotConfig cfg;
        cfg.policy = SlotPolicy::FIXED;
        cfg.fixedBinPercent = binPercent;
        cfg.maxSlots = limit;
        return cfg;
    }

    // Optional fluent setters (keep header-only for simplicity)
    SlotConfig& setGrowthEnabled(bool v)                 { growthEnabled = v; return *this; }
    SlotConfig& setNeuronGrowthEnabled(bool v)           { neuronGrowthEnabled = v; return *this; }
    SlotConfig& setLayerGrowthEnabled(bool v)            { layerGrowthEnabled = v; return *this; }
    SlotConfig& setFallbackGrowthThreshold(int v)        { fallbackGrowthThreshold = (v < 1 ? 1 : v); return *this; }
    SlotConfig& setNeuronGrowthCooldownTicks(int ticks)  { neuronGrowthCooldownTicks = (ticks < 0 ? 0 : ticks); return *this; }
};

} // namespace grownet
