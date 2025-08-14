#pragma once
#include <algorithm>
#include <cmath>

namespace grownet {
inline double smoothClamp(double x, double lo, double hi) {
    return std::max(lo, std::min(hi, x));
}
} // namespace grownet
