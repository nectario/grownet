#pragma once
#include <vector>
#include <memory>
#include "Layer.h"
#include "OutputNeuron.h"

namespace grownet {
/** Shape-aware output layer (e.g., image writer). */
class OutputLayer2D : public Layer {
    int height;
    int width;
    std::vector<std::vector<double>> frame;
public:
    OutputLayer2D(int h, int w, double smoothing)
        : Layer(0, 0, 0), height(h), width(w), frame(h, std::vector<double>(w, 0.0)) {
        auto& list = getNeurons();
        SlotConfig cfg = SlotConfig::fixed(10.0);
        for (int y = 0; y < height; ++y) {
            for (int x = 0; x < width; ++x) {
                list.push_back(std::make_shared<OutputNeuron>(
                    "OUT[" + std::to_string(y) + "," + std::to_string(x) + "]",
                    getBus(), cfg, smoothing));
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
        for (int idx = 0; idx < static_cast<int>(getNeurons().size()); ++idx) {
            auto n = std::static_pointer_cast<OutputNeuron>(getNeurons()[idx]);
            n->endTick();
            int y = idx / width, x = idx % width;
            frame[y][x] = n->getOutputValue();
        }
        Layer::endTick();
    }

    const std::vector<std::vector<double>>& getFrame() const { return frame; }
};
} // namespace grownet
