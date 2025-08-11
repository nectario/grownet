#include "Region.h"

namespace grownet {

Region::Region(std::string n) : name(std::move(n)) {}

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
    // Phase A: external input to entry layers (intra-layer propagation occurs immediately)
    auto it = inputPorts.find(port);
    if (it != inputPorts.end()) {
        for (int idx : it->second) {
            layers.at(idx)->forward(value);
        }
    }

    // Phase B: flush inter-layer tracts once
    int delivered = 0;
    for (auto& t : tracts) delivered += t->flush();

    // Decay
    for (auto& l : layers) l->getBus().decay();
    bus.decay();

    // Light metrics
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

PruneSummary Region::prune(long long synapseStaleWindow, double synapseMinStrength,
                           long long tractStaleWindow,   double tractMinStrength) {
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

void grownet::Region::setSlotPolicy(const SlotPolicyConfig& p){
    for (auto& l : layers){ l->setSlotPolicy(p); }
}
