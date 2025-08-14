#pragma once
#include <algorithm>
#include <cmath>

namespace grownet {
inline double smoothClamp(double x, double lo, double hi) {
    if (x < lo) return lo + (x - lo) * 0.5;
    if (x > hi) return hi + (x - hi) * 0.5;
    return x;
}
} // namespace grownet
