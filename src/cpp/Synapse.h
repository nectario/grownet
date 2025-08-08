#pragma once
#include "Weight.h"

namespace grownet {

    class Neuron; // forward declaration

    // Directed edge: source neuron --(weight)--> target neuron, with routing metadata.
    class Synapse {
    public:
        Synapse(Neuron* targetNeuron, bool feedbackFlag)
            : target(targetNeuron), isFeedback(feedbackFlag) {}

        Weight&       getWeight()      { return weight; }
        const Weight& getWeight() const{ return weight; }

        Neuron* getTarget() const      { return target; }
        bool    getIsFeedback() const  { return isFeedback; }

        long long lastStep {0};

    private:
        Weight  weight {};
        Neuron* target {nullptr};
        bool    isFeedback {false};
    };

} // namespace grownet
