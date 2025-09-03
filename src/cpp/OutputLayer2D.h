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
    OutputLayer2D(int heightPixels, int widthPixels, double smoothing)
        : Layer(0, 0, 0), height(heightPixels), width(widthPixels), frame(heightPixels, std::vector<double>(widthPixels, 0.0)) {
        auto& neuronList = getNeurons();
        SlotConfig cfg = SlotConfig::fixed(10.0);
        for (int row = 0; row < height; ++row) {
            for (int col = 0; col < width; ++col) {
                auto n = std::make_shared<OutputNeuron>(
                    "OUT[" + std::to_string(row) + "," + std::to_string(col) + "]",
                    getBus(), cfg, smoothing);
                n->setOwner(this);
                neuronList.push_back(n);
            }
        }
    }

    int index(int row, int col) const { return row * width + col; }

    // Accessors used by Region for deterministic windowed wiring
    int getHeight() const { return height; }
    int getWidth()  const { return width;  }

    void propagateFrom(int sourceIndex, double value) override {
        if (sourceIndex < 0 || sourceIndex >= static_cast<int>(getNeurons().size())) return;
        auto outputNeuron = std::static_pointer_cast<OutputNeuron>(getNeurons()[sourceIndex]);
        bool fired = outputNeuron->onInput(value);
        if (fired) outputNeuron->onOutput(value);
    }

    void endTick() override {
        for (int neuronIndex = 0; neuronIndex < static_cast<int>(getNeurons().size()); ++neuronIndex) {
            auto outputNeuron = std::static_pointer_cast<OutputNeuron>(getNeurons()[neuronIndex]);
            outputNeuron->endTick();
            int row = neuronIndex / width;
            int col = neuronIndex % width;
            frame[row][col] = outputNeuron->getOutputValue();
        }
        Layer::endTick();
    }

    const std::vector<std::vector<double>>& getFrame() const { return frame; }
};
} // namespace grownet
