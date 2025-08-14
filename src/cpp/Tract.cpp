#include "Tract.h"
#include <cmath>
#include <random>

namespace grownet {

void Tract::wireDenseRandom(double probability) {
    std::mt19937 rng(42);
    std::uniform_real_distribution<double> uni(0.0, 1.0);
    for (auto& sn : source->getNeurons()) {
        for (auto& dn : destination->getNeurons()) {
            if (sn.get() == dn.get()) continue;
            if (uni(rng) < probability) {
                edges.emplace_back(sn.get(), dn.get());
            }
        }
    }
}

void Tract::onSourceFired(Neuron* who, double amplitude) {
    for (auto& e : edges) {
        if (e.sourceNeuron != who) continue;
        e.weight.reinforce(regionBus->getModulationFactor());
        e.lastStep = regionBus->getCurrentStep();
        if (e.weight.updateThreshold(amplitude)) {
            queue.emplace(e.targetNeuron, amplitude);
        }
    }
}

int Tract::flush() {
    int delivered = 0;
    while (!queue.empty()) {
        auto ev = queue.front(); queue.pop();
        if (ev.target->onInput(ev.amplitude)) {
            ev.target->onOutput(ev.amplitude);
        }
        ++delivered;
    }
    return delivered;
}

} // namespace grownet
