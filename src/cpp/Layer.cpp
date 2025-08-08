#include "Layer.h"

namespace grownet {

Layer::Layer(int excitatoryCount, int inhibitoryCount, int modulatoryCount) {
    std::random_device randomDevice;
    randomGenerator.seed(randomDevice());

    for (int index = 0; index < excitatoryCount; ++index) {
        neurons.push_back(std::make_unique<ExcitatoryNeuron>("E" + std::to_string(index), &bus));
    }
    for (int index = 0; index < inhibitoryCount; ++index) {
        neurons.push_back(std::make_unique<InhibitoryNeuron>("I" + std::to_string(index), &bus));
    }
    for (int index = 0; index < modulatoryCount; ++index) {
        neurons.push_back(std::make_unique<ModulatoryNeuron>("M" + std::to_string(index), &bus));
    }
}

void Layer::wireRandomFeedforward(double probability) {
    if (probability <= 0.0) return;
    const std::size_t neuronCount = neurons.size();
    for (std::size_t sourceIndex = 0; sourceIndex < neuronCount; ++sourceIndex) {
        for (std::size_t targetIndex = 0; targetIndex < neuronCount; ++targetIndex) {
            if (sourceIndex == targetIndex) continue;
            if (uniform01(randomGenerator) < probability) {
                neurons[sourceIndex]->connect(neurons[targetIndex].get(), false);
            }
        }
    }
}

void Layer::wireRandomFeedback(double probability) {
    if (probability <= 0.0) return;
    const std::size_t neuronCount = neurons.size();
    for (std::size_t sourceIndex = 0; sourceIndex < neuronCount; ++sourceIndex) {
        for (std::size_t targetIndex = 0; targetIndex < neuronCount; ++targetIndex) {
            if (sourceIndex == targetIndex) continue;
            if (uniform01(randomGenerator) < probability) {
                neurons[targetIndex]->connect(neurons[sourceIndex].get(), true);
            }
        }
    }
}

void Layer::forward(double value) {
    for (auto& neuronItem : neurons) {
        neuronItem->onInput(value);
    }
    bus.decay();
    for (auto& neuronItem : neurons) {
        neuronItem->pruneSynapses(bus.getCurrentStep(), 10'000, 0.05);
    }
}

} // namespace grownet
