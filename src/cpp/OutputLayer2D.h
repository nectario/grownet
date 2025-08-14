#pragma once
#include <memory>
#include <vector>
#include <string>
#include "Layer.h"
#include "OutputNeuron.h"

namespace grownet {

class OutputLayer2D : public Layer {
public:
    OutputLayer2D(int height, int width, double smoothing)
        : Layer(0,0,0), height(height), width(width), frame(height, std::vector<double>(width, 0.0)) {
        auto& list = getNeurons();
        for (int y = 0; y < height; ++y) {
            for (int x = 0; x < width; ++x) {
                list.push_back(std::make_shared<OutputNeuron>(
                    "OUT[" + std::to_string(y) + "," + std::to_string(x) + "]",
                    getBus(), smoothing));
            }
        }
    }

    int index(int y, int x) const { return y * width + x; }

    void propagateFrom(int sourceIndex, double value) override {
        if (sourceIndex < 0 || sourceIndex >= static_cast<int>(getNeurons().size())) return;
        auto n = std::static_pointer_cast<OutputNeuron>(getNeurons()[sourceIndex]);
        bool fired = n->onInput(value);
        if (fired) n->onOutput(value);
    }

    void endTick() override {
        Layer::endTick();
        for (int idx = 0; idx < static_cast<int>(getNeurons().size()); ++idx) {
            auto n = std::static_pointer_cast<OutputNeuron>(getNeurons()[idx]);
            int y = idx / width;
            int x = idx % width;
            frame[y][x] = n->getOutputValue();
        }
    }

    const std::vector<std::vector<double>>& getFrame() const { return frame; }

private:
    int height;
    int width;
    std::vector<std::vector<double>> frame;
};

} // namespace grownet