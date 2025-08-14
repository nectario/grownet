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
    Synapse(Neuron* src, Neuron* dst, bool fb) : source(src), target(dst), feedback(fb) {}
};
} // namespace grownet
