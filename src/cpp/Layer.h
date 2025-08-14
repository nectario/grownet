#pragma once
#include <memory>
#include <random>
#include <vector>

#include "LateralBus.h"
#include "Neuron.h"
#include "SlotConfig.h"

namespace grownet {

class Layer {
public:
    Layer(int excitatoryCount, int inhibitoryCount, int modulatoryCount)
    {
        SlotConfig cfg = SlotConfig::fixed(10.0);
        int slotLimit = -1;
        neurons.reserve(excitatoryCount + inhibitoryCount + modulatoryCount);
        for (int i = 0; i < excitatoryCount; ++i) {
            neurons.push_back(std::make_shared<ExcitatoryNeuron>("E"+std::to_string(i), bus, cfg, slotLimit));
        }
        for (int i = 0; i < inhibitoryCount; ++i) {
            neurons.push_back(std::make_shared<InhibitoryNeuron>("I"+std::to_string(i), bus, cfg, slotLimit));
        }
        for (int i = 0; i < modulatoryCount; ++i) {
            neurons.push_back(std::make_shared<ModulatoryNeuron>("M"+std::to_string(i), bus, cfg, slotLimit));
        }
    }

    std::vector<std::shared_ptr<Neuron>>& getNeurons() { return neurons; }
    LateralBus& getBus() { return bus; }

    void wireRandomFeedforward(double probability) {
        std::mt19937 rng{1234};
        std::uniform_real_distribution<double> uni(0.0, 1.0);
        for (auto& a : neurons) {
            for (auto& b : neurons) {
                if (a.get() == b.get()) continue;
                if (uni(rng) < probability) a->connect(b.get(), /*feedback=*/false);
            }
        }
    }
    void wireRandomFeedback(double probability) {
        std::mt19937 rng{4321};
        std::uniform_real_distribution<double> uni(0.0, 1.0);
        for (auto& a : neurons) {
            for (auto& b : neurons) {
                if (a.get() == b.get()) continue;
                if (uni(rng) < probability) a->connect(b.get(), /*feedback=*/true);
            }
        }
    }

    void forward(double value) {
        for (auto& n : neurons) {
            bool fired = n->onInput(value);
            if (fired) n->onOutput(value);
        }
    }

    void endTick() { bus.decay(); }

private:
    std::vector<std::shared_ptr<Neuron>> neurons;
    LateralBus bus;
};

} // namespace grownet
