#pragma once
#include <cstddef>

namespace grownet {
class Neuron;

/** Minimal outgoing connection record. */
struct Synapse {
    Neuron* source { nullptr };
    Neuron* target { nullptr };
    bool    feedback { false };

    Synapse() = default;
    Synapse(Neuron* sourceNeuron, Neuron* targetNeuron, bool isFeedback)
        : source(sourceNeuron), target(targetNeuron), feedback(isFeedback) {}
};
} // namespace grownet
