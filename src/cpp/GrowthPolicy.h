#pragma once

namespace grownet {

struct GrowthPolicy {
    bool   enableRegionGrowth     { true };
    int    maximumLayers          { -1 };     // -1 = unlimited
    double averageSlotsThreshold  { 12.0 };
    // Optional OR-trigger: if > 0, grow when percent of neurons that are at capacity
    // and used a fallback slot this tick is >= this threshold.
    double percentAtCapFallbackThreshold { 0.0 };
    int    layerCooldownTicks     { 50 };
    double connectionProbability  { 1.0 };
    bool   preferMostSaturated    { true };
    unsigned int rngSeed          { 1234U };
};

} // namespace grownet
