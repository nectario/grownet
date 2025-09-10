// Deterministic 3D layout for proximity policy (pure function; no core fields changed).
#pragma once
#include <cmath>
#include <tuple>
#include <string>

namespace grownet {

struct DeterministicLayout {
    static constexpr double layerSpacing = 4.0;
    static constexpr double gridSpacing  = 1.2;

    static inline std::tuple<double,double,double>
    position(const std::string& /*regionName*/, int layerIndex, int neuronIndex, int layerHeight = 0, int layerWidth = 0) {
        if (layerHeight > 0 && layerWidth > 0) {
            const int rowIndex = neuronIndex / layerWidth;
            const int colIndex = neuronIndex % layerWidth;
            const double offsetX = (colIndex - (layerWidth - 1) / 2.0) * gridSpacing;
            const double offsetY = ((layerHeight - 1) / 2.0 - rowIndex) * gridSpacing;
            const double offsetZ = static_cast<double>(layerIndex) * layerSpacing;
            return { offsetX, offsetY, offsetZ };
        }
        const int plusOne = neuronIndex + 1;
        int gridSide = static_cast<int>(std::sqrt(static_cast<double>(plusOne)));
        if (gridSide * gridSide < plusOne) ++gridSide;
        const int rowIndex2 = neuronIndex / gridSide;
        const int colIndex2 = neuronIndex % gridSide;
        const double offsetX2 = (colIndex2 - (gridSide - 1) / 2.0) * gridSpacing;
        const double offsetY2 = ((gridSide - 1) / 2.0 - rowIndex2) * gridSpacing;
        const double offsetZ2 = static_cast<double>(layerIndex) * layerSpacing;
        return { offsetX2, offsetY2, offsetZ2 };
    }
};

} // namespace grownet
