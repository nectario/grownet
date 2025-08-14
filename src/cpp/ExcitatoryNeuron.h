#pragma once
#include "Neuron.h"
namespace grownet {
class ExcitatoryNeuron : public Neuron {
public:
    using Neuron::Neuron; // inherit constructor
    // default fire() is excitatory; no override needed
};
} // namespace grownet
