#include "Tract.h"
#include <random>

namespace grownet {

Tract::Tract(std::shared_ptr<Layer> src,
             std::shared_ptr<Layer> dst,
             RegionBus& bus,
             bool fb)
    : source(std::move(src)), destination(std::move(dst)), regionBus(bus), feedback(fb) {}

void Tract::wireDenseRandom(double probability) {
    if (probability <= 0.0) return;

    std::random_device rd;
    std::mt19937_64 gen(rd());
    std::uniform_real_distribution<double> uni(0.0, 1.0);

    for (const auto& src : source->getNeurons()) {
        for (const auto& dst : destination->getNeurons()) {
            if (src.get() == dst.get()) continue;
            if (uni(gen) >= probability)  continue;

            edges[src.get()].push_back(InterLayerEdge{dst, Weight{}, feedback, 0});

            if (!hookedSources.count(src.get())) {
                src->registerFireHook(makeSourceHook(src.get()));
                hookedSources.insert(src.get());
            }
        }
    }
}

FireHook Tract::makeSourceHook(Neuron* src) {
    return [this, src](double inputValue, Neuron& self) {
        if (&self != src) return;
        auto it = edges.find(src);
        if (it == edges.end()) return;

        for (auto& edge : it->second) {
            edge.weight.reinforce(regionBus.getModulationFactor(),
                                  regionBus.getInhibitionFactor());
            bool fired = edge.weight.updateThreshold(inputValue);
            if (fired) {
                queue.push_back(QueuedEvent{edge.target, inputValue});
                edge.lastStep = regionBus.getCurrentStep();
            }
        }
    };
}

int Tract::flush() {
    if (queue.empty()) return 0;
    std::vector<QueuedEvent> pending;
    pending.swap(queue);
    int delivered = 0;
    for (const auto& ev : pending) {
        ev.target->onInput(ev.value);
        ++delivered;
    }
    return delivered;
}

int Tract::pruneEdges(long long staleWindow, double minStrength) {
    int pruned = 0;
    for (auto& kv : edges) {
        auto& vec = kv.second;
        auto newEnd = std::remove_if(vec.begin(), vec.end(), [&](const InterLayerEdge& e) {
            bool stale = (regionBus.getCurrentStep() - e.lastStep) > staleWindow;
            bool weak  = e.weight.getStrengthValue() < minStrength;
            return stale && weak;
        });
        pruned += static_cast<int>(vec.end() - newEnd);
        vec.erase(newEnd, vec.end());
    }
    return pruned;
}

} // namespace grownet
