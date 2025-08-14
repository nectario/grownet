#pragma once
#include "Weight.h"

namespace grownet {
class Neuron;
struct Synapse {
    Neuron* source { nullptr };
    Neuron* target { nullptr };
    bool feedback { false };
    Weight weight;

    Synapse(Neuron* s=nullptr, Neuron* t=nullptr, bool fb=false)
      : source(s), target(t), feedback(fb) {}
};
} // namespace grownet
