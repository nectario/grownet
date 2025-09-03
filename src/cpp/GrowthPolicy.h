#pragma once

namespace grownet {

struct GrowthPolicy {
    bool   enableRegionGrowth     { true };
    int    maximumLayers          { -1 };     // -1 = unlimited
    double averageSlotsThreshold  { 12.0 };
    int    layerCooldownTicks     { 50 };
    double connectionProbability  { 1.0 };
    bool   preferMostSaturated    { true };
    unsigned int rngSeed          { 1234U };
};

} // namespace grownet

