
#pragma once
#include "Neuron.h"

namespace grownet {
class ModulatoryNeuron : public Neuron {
public:
    using Neuron::Neuron;
    void setKappa(double k) { kappa = k; }
    void fire(double inputValue) override {
        if (bus) bus->setModulationFactor(kappa);
        // Do not propagate further; this is a neuromodulatory pulse
        (void)inputValue;
    }
private:
    double kappa {1.5}; // scales learning step at bus level
};
} // namespace grownet
