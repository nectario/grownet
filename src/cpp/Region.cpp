
#include "Region.h"

namespace grownet {

Region::Region(std::string regionName) : name(std::move(regionName)) {}

int Region::addLayer(int excitatoryCount, int inhibitoryCount, int modulatoryCount) {
    auto layer = std::make_shared<Layer>(excitatoryCount, inhibitoryCount, modulatoryCount);
    layers.push_back(layer);
    return static_cast<int>(layers.size()) - 1;
}

Tract& Region::connectLayers(int sourceIndex, int destIndex, double probability, bool feedback) {
    auto src = layers.at(sourceIndex);
    auto dst = layers.at(destIndex);
    auto tract = std::make_unique<Tract>(src, dst, bus, feedback);
    tract->wireDenseRandom(probability);
    tracts.push_back(std::move(tract));
    return *tracts.back();
}

void Region::bindInput(const std::string& port, const std::vector<int>& layerIndices) {
    inputPorts[port] = layerIndices;
}

void Region::bindOutput(const std::string& port, const std::vector<int>& layerIndices) {
    outputPorts[port] = layerIndices;
}

RegionMetrics Region::tick(const std::string& port, double value) {
    auto it = inputPorts.find(port);
    if (it != inputPorts.end()) {
        for (int idx : it->second) {
            layers.at(idx)->forward(value);
        }
    }

    int delivered = 0;
    for (auto& t : tracts) delivered += t->flush();

    for (auto& l : layers) l->getBus().decay();
    bus.decay();

    int totalSlots = 0;
    int totalSynapses = 0;
    for (auto& l : layers) {
        for (const auto& n : l->getNeurons()) {
            totalSlots    += static_cast<int>(n->getSlots().size());
            totalSynapses += static_cast<int>(n->getOutgoing().size());
        }
    }
    return RegionMetrics{delivered, totalSlots, totalSynapses};
}

PruneSummary Region::prune(std::int64_t synapseStaleWindow, double synapseMinStrength,
                           std::int64_t tractStaleWindow,   double tractMinStrength) {
    int prunedSyn = 0;
    for (auto& l : layers) {
        for (const auto& n : l->getNeurons()) {
            int before = static_cast<int>(n->getOutgoing().size());
            n->pruneSynapses(bus.getCurrentStep(), synapseStaleWindow, synapseMinStrength);
            prunedSyn += before - static_cast<int>(n->getOutgoing().size());
        }
    }
    int prunedEdges = 0;
    for (auto& t : tracts) prunedEdges += t->pruneEdges(tractStaleWindow, tractMinStrength);
    return PruneSummary{prunedSyn, prunedEdges};
}

} // namespace grownet
