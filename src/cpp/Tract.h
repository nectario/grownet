#pragma once
#include <memory>
#include <random>
#include <unordered_map>
#include "Layer.h"
#include "RegionBus.h"

namespace grownet {
/** Connects two layers within a Region by registering spike hooks. */
class Tract {
    Layer* source { nullptr };
    Layer* dest   { nullptr };
    RegionBus* regionBus { nullptr };
    bool feedback { false };
    double probability { 1.0 };
    std::mt19937 rng { 1337 };
public:
    Tract(Layer* sourceLayer, Layer* destLayer, RegionBus* regionBusPtr, bool isFeedback, double connectProbability)
        : source(sourceLayer), dest(destLayer), regionBus(regionBusPtr), feedback(isFeedback), probability(connectProbability) {
        std::uniform_real_distribution<double> uni(0.0, 1.0);
        auto& srcNeurons = source->getNeurons();
        for (int index = 0; index < static_cast<int>(srcNeurons.size()); ++index) {
            if (uni(rng) > probability) continue;
            auto nPtr = srcNeurons[index];
            nPtr->registerFireHook([this, index](Neuron* /*who*/, double amplitude) {
                (void)feedback;
                (void)regionBus;
                if (dest) dest->propagateFrom(index, amplitude);
            });
        }
    }

    // Accessors used by Region for growth auto-subscription
    Layer* getSourceLayer() const { return source; }
    Layer* getDestLayer()   const { return dest; }

    /** Subscribe a newly created source neuron so its spikes propagate through this tract. */
    void attachSourceNeuron(int newSourceIndex);
};
} // namespace grownet
