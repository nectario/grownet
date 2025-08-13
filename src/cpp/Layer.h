
#pragma once
#include <vector>
#include <memory>
#include <random>

#include "LateralBus.h"
#include "Neuron.h"
#include "ExcitatoryNeuron.h"
#include "InhibitoryNeuron.h"
#include "ModulatoryNeuron.h"

namespace grownet {

class Layer {
public:
    Layer(int excitatoryCount, int inhibitoryCount, int modulatoryCount);

    LateralBus& getBus() { return bus; }
    const std::vector<std::unique_ptr<Neuron>>& getNeurons() const { return neurons; }
    std::vector<std::unique_ptr<Neuron>>&       getNeurons()       { return neurons; }

    void wireRandomFeedforward(double probability);
    void wireRandomFeedback(double probability);

    void forward(double value);

private:
    LateralBus bus {};
    std::vector<std::unique_ptr<Neuron>> neurons;

    std::mt19937_64 randomGenerator;
    std::uniform_real_distribution<double> uniform01 {0.0, 1.0};
};

} // namespace grownet
