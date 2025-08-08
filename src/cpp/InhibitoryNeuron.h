#pragma once
#include "Neuron.h"

namespace grownet {

    class InhibitoryNeuron : public Neuron {
    public:
        using Neuron::Neuron;

        void fire(double inputValue) override;
    };

} // namespace grownet
