#pragma once
#include <algorithm>
#include <cmath>

namespace grownet {
inline double smoothClamp(double value, double low, double high) {
    return std::max(low, std::min(high, value));
}
} // namespace grownet
