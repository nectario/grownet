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
    InputLayer2D(int h, int w, double gain, double epsilonFire)
        : Layer(0, 0, 0), height(h), width(w) {
        auto& list = getNeurons();
        SlotConfig cfg = SlotConfig::fixed(10.0);
        for (int y = 0; y < height; ++y) {
            for (int x = 0; x < width; ++x) {
                list.push_back(std::make_shared<InputNeuron>(
                    "IN[" + std::to_string(y) + "," + std::to_string(x) + "]",
                    getBus(), cfg, gain, epsilonFire));
            }
        }
    }

    int index(int y, int x) const { return y * width + x; }

    void forwardImage(const std::vector<std::vector<double>>& frame) {
        auto& list = getNeurons();
        for (int y = 0; y < height; ++y) {
            for (int x = 0; x < width; ++x) {
                int idx = index(y, x);
                auto n = std::static_pointer_cast<InputNeuron>(list[idx]);
                n->onInput(frame[y][x]);
            }
        }
    }

    void propagateFrom(int /*sourceIndex*/, double /*value*/) override {
        // No-op: Input layer is an entry-point in this demo.
    }
};
} // namespace grownet
