#pragma once
#include <vector>
#include <queue>
#include <random>
#include <memory>

#include "Layer.h"
#include "RegionBus.h"
#include "Neuron.h"

namespace grownet {

class Tract {
public:
    Tract(Layer& src, Layer& dst, RegionBus& bus, bool fb)
        : source(&src), destination(&dst), regionBus(&bus), feedback(fb) {
        // Register hooks on already-existing source neurons
        for (auto& nPtr : source->getNeurons()) {
            nPtr->registerFireHook([this](Neuron* who, double value) {
                this->onSourceFired(who, value);
            });
        }
    }

    // Random wiring (dense; demo-friendly)
    void wireDenseRandom(double probability);

    // Flush queued events; return number delivered
    int flush();

private:
    struct Edge {
        Neuron* sourceNeuron { nullptr };
        Neuron* targetNeuron { nullptr };
        Weight  weight;
        long long lastStep {0};

        Edge(Neuron* s, Neuron* t) : sourceNeuron(s), targetNeuron(t) {}
    };

    void onSourceFired(Neuron* who, double amplitude);

private:
    Layer*    source { nullptr };
    Layer*    destination { nullptr };
    RegionBus* regionBus { nullptr };
    bool      feedback { false };

    std::vector<Edge> edges;

    struct Event {
        Neuron* target { nullptr };
        double amplitude { 0.0 };
        Event(Neuron* t, double a) : target(t), amplitude(a) {}
    };
    std::queue<Event> queue;
};

} // namespace grownet
