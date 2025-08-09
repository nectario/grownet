#pragma once
#include <vector>
#include <memory>
#include "Layer.h"
#include "InputNeuron.h"

namespace grownet {

class InputLayer2D : public Layer {
public:
    InputLayer2D(int height, int width, double gain = 1.0, double epsilonFire = 0.01)
        : Layer(0,0,0), height(height), width(width) {
        auto& list = getNeurons();
        for (int y = 0; y < height; ++y) {
            for (int x = 0; x < width; ++x) {
                list.push_back(std::make_shared<InputNeuron>(
                    "IN[" + std::to_string(y) + "," + std::to_string(x) + "]",
                    gain, epsilonFire));
            }
        }
    }

    int index(int y, int x) const { return y * width + x; }

    void forwardImage(const std::vector<std::vector<double>>& image) {
        for (int y = 0; y < height; ++y) {
            for (int x = 0; x < width; ++x) {
                int idx = index(y, x);
                auto n = std::static_pointer_cast<InputNeuron>(getNeurons()[idx]);
                bool fired = n->onInput(image[y][x], getBus());
                if (fired) n->onOutput(image[y][x]);
            }
        }
    }

    void propagateFrom(int sourceIndex, double /*value*/) override {
        // entry layer: no intra-layer routing
    }

private:
    int height, width;
};

} // namespace grownet
