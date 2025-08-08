#pragma once
#include "Neuron.h"

namespace grownet {

    class ExcitatoryNeuron : public Neuron {
    public:
        using Neuron::Neuron; // inherit constructor
        // Inherits default fire()
    };

} // namespace grownet
