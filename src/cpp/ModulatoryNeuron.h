#pragma once
#include "Neuron.h"

namespace grownet {

    class ModulatoryNeuron : public Neuron {
    public:
        using Neuron::Neuron;

        void fire(double inputValue) override;
    };

} // namespace grownet
