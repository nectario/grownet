#pragma once
#include <algorithm>

namespace grownet {

    inline double smoothStep(double edgeStart, double edgeEnd, double value) {
        if (edgeEnd == edgeStart) return 0.0;
        double t = (value - edgeStart) / (edgeEnd - edgeStart);
        t = std::clamp(t, 0.0, 1.0);
        return t * t * (3.0 - 2.0 * t);
    }

    inline double smoothClamp(double value, double lower, double upper) {
        return smoothStep(0.0, 1.0, (value - lower) / (upper - lower)) * (upper - lower) + lower;
    }

} // namespace grownet
