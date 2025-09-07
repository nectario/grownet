// File: src/cpp/include/DeterministicLayout.h
#pragma once
#include <tuple>
#include <cmath>
#include <string>

struct DeterministicLayout {
    static constexpr double LAYER_SPACING = 4.0;
    static constexpr double GRID_SPACING  = 1.2;

    static std::tuple<double,double,double>
    position(const std::string& regionName, int layerIndex, int neuronIndex, int layerHeight, int layerWidth) {
        if (layerHeight > 0 && layerWidth > 0) {
            int rowIndex = neuronIndex / layerWidth;
            int colIndex = neuronIndex % layerWidth;
            double xCoord = (colIndex - (layerWidth - 1) / 2.0) * GRID_SPACING;
            double yCoord = ((layerHeight - 1) / 2.0 - rowIndex) * GRID_SPACING;
            double zCoord = static_cast<double>(layerIndex) * LAYER_SPACING;
            return {xCoord, yCoord, zCoord};
        }
        int gridSide = static_cast<int>(std::sqrt(neuronIndex + 1));
        if (gridSide * gridSide < neuronIndex + 1) gridSide += 1;
        int rowIndex = neuronIndex / gridSide;
        int colIndex = neuronIndex % gridSide;
        double xCoord = (colIndex - (gridSide - 1) / 2.0) * GRID_SPACING;
        double yCoord = ((gridSide - 1) / 2.0 - rowIndex) * GRID_SPACING;
        double zCoord = static_cast<double>(layerIndex) * LAYER_SPACING;
        return {xCoord, yCoord, zCoord};
    }
};
