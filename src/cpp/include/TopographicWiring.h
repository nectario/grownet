#pragma once
#include <string>

namespace grownet {
class Region;

struct TopographicConfig {
    int kernel_h {7};
    int kernel_w {7};
    int stride_h {1};
    int stride_w {1};
    std::string padding {"same"};
    bool feedback { false };
    std::string weight_mode {"gaussian"}; // or "dog"
    double sigma_center { 2.0 };
    double sigma_surround { 4.0 };
    double surround_ratio { 0.5 };
    bool normalize_incoming { true };
};

// Returns unique source subscriptions (same as connectLayersWindowed)
int connectLayersTopographic(Region& region,
                             int sourceLayerIndex,
                             int destinationLayerIndex,
                             const TopographicConfig& config);

} // namespace grownet

