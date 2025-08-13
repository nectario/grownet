
#pragma once
#include <cstdint>
#include "Weight.h"

namespace grownet {

class Neuron; // forward declaration

class Synapse {
public:
    Synapse(Neuron* targetPtr = nullptr, bool feedbackEdge = false)
        : target(targetPtr), isFeedback(feedbackEdge) {}

    Neuron* getTarget() const { return target; }
    Weight& getWeight() { return weight; }
    const Weight& getWeight() const { return weight; }

    bool getIsFeedback() const { return isFeedback; }

    std::int64_t lastStep {0}; // last time this synapse carried a spike

private:
    Neuron* target {nullptr};
    Weight  weight {};
    bool    isFeedback {false};
};

} // namespace grownet
