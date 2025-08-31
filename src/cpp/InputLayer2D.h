#pragma once
#include <vector>
#include <memory>
#include "Layer.h"
#include "InputNeuron.h"

namespace grownet {
/** Shape-aware source layer that consumes 2D frames. */
class InputLayer2D : public Layer {
    int height;
    int width;
public:
    InputLayer2D(int heightPixels, int widthPixels, double gain, double epsilonFire)
        : Layer(0, 0, 0), height(heightPixels), width(widthPixels) {
        auto& neuronList = getNeurons();
        SlotConfig cfg = SlotConfig::fixed(10.0);
        for (int row = 0; row < height; ++row) {
            for (int col = 0; col < width; ++col) {
                neuronList.push_back(std::make_shared<InputNeuron>(
                    "IN[" + std::to_string(row) + "," + std::to_string(col) + "]",
                    getBus(), cfg, gain, epsilonFire));
            }
        }
    }

    int index(int row, int col) const { return row * width + col; }

    // Deliver a 2D frame (row-major) to matching input neurons.
    void forwardImage(const std::vector<std::vector<double>>& frame) {
        auto& neuronList = getNeurons();
        for (int row = 0; row < height; ++row) {
            for (int col = 0; col < width; ++col) {
                int neuronIndex = index(row, col);
                auto inputNeuron = std::static_pointer_cast<InputNeuron>(neuronList[neuronIndex]);
                inputNeuron->onInput(frame[row][col]);
            }
        }
    }

    void propagateFrom(int /*sourceIndex*/, double /*value*/) override {
        // No-op: Input layer is an entry-point in this demo.
    }
};
} // namespace grownet
