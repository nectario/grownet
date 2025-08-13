
#pragma once
#include "Neuron.h"

namespace grownet {
class ExcitatoryNeuron : public Neuron {
public:
    using Neuron::Neuron; // inherit constructor
    void fire(double inputValue) override { Neuron::fire(inputValue); }
};
} // namespace grownet
