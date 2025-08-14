#include "Region.h"

namespace grownet {

Tract& Region::connectLayers(int sourceIndex, int destIndex, double probability, bool feedback) {
    if (sourceIndex < 0 || sourceIndex >= static_cast<int>(layers.size()))
        throw std::out_of_range("sourceIndex out of range");
    if (destIndex < 0 || destIndex >= static_cast<int>(layers.size()))
        throw std::out_of_range("destIndex out of range");

    auto& src = *layers[sourceIndex];
    auto& dst = *layers[destIndex];
    tracts.push_back(std::make_unique<Tract>(src, dst, bus, feedback));
    auto& t = *tracts.back();
    t.wireDenseRandom(probability);
    return t;
}

RegionMetrics Region::tick(const std::string& port, double value) {
    RegionMetrics m;

    auto it = inputPorts.find(port);
    if (it != inputPorts.end()) {
        for (int layerIdx : it->second) {
            layers[layerIdx]->forward(value);
            m.deliveredEvents += 1; // lightweight placeholder
        }
    }

    // Flush tracts
    for (auto& t : tracts) m.deliveredEvents += t->flush();

    // end-of-tick housekeeping for all layers
    for (auto& layer : layers) layer->endTick();

    // simple aggregate metrics for dashboards
    for (auto& layer : layers) {
        for (auto& n : layer->getNeurons()) {
            m.totalSlots    += static_cast<int>(n->getSlots().size());
            m.totalSynapses += static_cast<int>(n->getOutgoing().size());
        }
    }
    return m;
}

} // namespace grownet
