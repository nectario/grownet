#pragma once
#include <string>

namespace grownet {
class Region;

struct TopographicConfig {
    int kernelH {7};
    int kernelW {7};
    int strideH {1};
    int strideW {1};
    std::string padding {"same"};
    bool feedback { false };
    std::string weightMode {"gaussian"}; // or "dog"
    double sigmaCenter { 2.0 };
    double sigmaSurround { 4.0 };
    double surroundRatio { 0.5 };
    bool normalizeIncoming { true };
};

// Returns unique source subscriptions (same as connectLayersWindowed)
int connectLayersTopographic(Region& region,
                             int sourceLayerIndex,
                             int destinationLayerIndex,
                             const TopographicConfig& config);

} // namespace grownet
