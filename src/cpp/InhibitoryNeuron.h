
#pragma once
#include "Neuron.h"

namespace grownet {
class InhibitoryNeuron : public Neuron {
public:
    using Neuron::Neuron;
    void setGamma(double g) { gamma = g; }
    void fire(double inputValue) override {
        if (bus) bus->setInhibitionFactor(gamma);
        // Do not propagate downstream for pure inhibition spike
        (void)inputValue;
    }
private:
    double gamma {0.7}; // multiplicative damping applied at bus level
};
} // namespace grownet
