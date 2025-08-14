#include "Region.h"
#include <stdexcept>

namespace grownet {

Region::Region(std::string name) : name(std::move(name)) {}

int Region::addLayer(int excitatoryCount, int inhibitoryCount, int modulatoryCount) {
    layers.push_back(std::make_shared<Layer>(excitatoryCount, inhibitoryCount, modulatoryCount));
    return static_cast<int>(layers.size() - 1);
}

int Region::addInputLayer2D(int h, int w, double gain, double epsilonFire) {
    layers.push_back(std::make_shared<InputLayer2D>(h, w, gain, epsilonFire));
    return static_cast<int>(layers.size() - 1);
}

int Region::addOutputLayer2D(int h, int w, double smoothing) {
    layers.push_back(std::make_shared<OutputLayer2D>(h, w, smoothing));
    return static_cast<int>(layers.size() - 1);
}

Tract& Region::connectLayers(int sourceIndex, int destIndex, double probability, bool feedback) {
    if (sourceIndex < 0 || sourceIndex >= static_cast<int>(layers.size()))
        throw std::out_of_range("sourceIndex out of range");
    if (destIndex < 0 || destIndex >= static_cast<int>(layers.size()))
        throw std::out_of_range("destIndex out of range");

    auto tract = std::make_unique<Tract>(layers[sourceIndex].get(), layers[destIndex].get(), &bus, feedback, probability);
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
    RegionMetrics metrics;
    auto it = inputPorts.find(port);
    if (it != inputPorts.end()) {
        for (int layerIndex : it->second) {
            layers[layerIndex]->forward(value);
            metrics.deliveredEvents += 1;
            metrics.delivered_events += 1; // legacy alias
        }
    }
    for (auto& layer : layers) layer->endTick();
    for (auto& layer : layers) {
        for (auto& neuron : layer->getNeurons()) {
            metrics.totalSlots    += static_cast<int>(neuron->getSlots().size());
            metrics.totalSynapses += static_cast<int>(neuron->getOutgoing().size());
        }
    }
    return metrics;
}

RegionMetrics Region::tickImage(const std::string& port, const std::vector<std::vector<double>>& frame) {
    RegionMetrics metrics;
    auto it = inputPorts.find(port);
    if (it != inputPorts.end()) {
        for (int layerIndex : it->second) {
            auto layerPtr = layers[layerIndex];
            auto inputLayer = std::dynamic_pointer_cast<InputLayer2D>(layerPtr);
            if (inputLayer) {
                inputLayer->forwardImage(frame);
                metrics.deliveredEvents += 1;
                metrics.delivered_events += 1;
            }
        }
    }
    for (auto& layer : layers) layer->endTick();
    for (auto& layer : layers) {
        for (auto& neuron : layer->getNeurons()) {
            metrics.totalSlots    += static_cast<int>(neuron->getSlots().size());
            metrics.totalSynapses += static_cast<int>(neuron->getOutgoing().size());
        }
    }
    return metrics;
}

} // namespace grownet
