
#include "Layer.h"
#include <string>

namespace grownet {

Layer::Layer(int excitatoryCount, int inhibitoryCount, int modulatoryCount) {
    std::random_device rd;
    randomGenerator.seed(rd());

    for (int i = 0; i < excitatoryCount; ++i) {
        neurons.push_back(std::make_unique<ExcitatoryNeuron>("E" + std::to_string(i), &bus));
    }
    for (int i = 0; i < inhibitoryCount; ++i) {
        neurons.push_back(std::make_unique<InhibitoryNeuron>("I" + std::to_string(i), &bus));
    }
    for (int i = 0; i < modulatoryCount; ++i) {
        neurons.push_back(std::make_unique<ModulatoryNeuron>("M" + std::to_string(i), &bus));
    }
}

void Layer::wireRandomFeedforward(double probability) {
    if (probability <= 0.0) return;
    const std::size_t n = neurons.size();
    for (std::size_t s = 0; s < n; ++s) {
        for (std::size_t t = 0; t < n; ++t) {
            if (s == t) continue;
            if (uniform01(randomGenerator) < probability) {
                neurons[s]->connect(neurons[t].get(), false);
            }
        }
    }
}

void Layer::wireRandomFeedback(double probability) {
    if (probability <= 0.0) return;
    const std::size_t n = neurons.size();
    for (std::size_t s = 0; s < n; ++s) {
        for (std::size_t t = 0; t < n; ++t) {
            if (s == t) continue;
            if (uniform01(randomGenerator) < probability) {
                neurons[t]->connect(neurons[s].get(), true);
            }
        }
    }
}

void Layer::forward(double value) {
    for (auto& n : neurons) n->onInput(value);
    bus.decay();
    for (auto& n : neurons) n->pruneSynapses(bus.getCurrentStep(), 10000, 0.05);
}

} // namespace grownet
