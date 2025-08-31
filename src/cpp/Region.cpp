#include "Region.h"
#include "InputLayerND.h"
#include <random>

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

    // NOTE: pass 'probability' to Tract ctor; it wires internally.
    auto tract = std::make_unique<Tract>(
        layers[sourceIndex].get(),
        layers[destIndex].get(),
        &bus,
        feedback,
        probability
    );

    tracts.push_back(std::move(tract));
    return *tracts.back();
}


// ---------------- edge helpers ----------------

int Region::ensureInputEdge(const std::string& port) {
    auto edgeIt = inputEdges.find(port);
    if (edgeIt != inputEdges.end()) return edgeIt->second;
    int edgeIndex = addLayer(1, 0, 0); // 1-neuron scalar input edge
    inputEdges[port] = edgeIndex;
    return edgeIndex;
}

int Region::ensureOutputEdge(const std::string& port) {
    auto edgeIt = outputEdges.find(port);
    if (edgeIt != outputEdges.end()) return edgeIt->second;
    int edgeIndex = addLayer(1, 0, 0); // 1-neuron scalar output sink
    outputEdges[port] = edgeIndex;
    return edgeIndex;
}

// ---------------- bindings ----------------

void Region::bindInput(const std::string& port, const std::vector<int>& layerIndices) {
    inputPorts[port] = layerIndices;
    int inEdge = ensureInputEdge(port);
    for (int layerIndex : layerIndices) {
        connectLayers(inEdge, layerIndex, /*probability=*/1.0, /*feedback=*/false);
    }
}

void Region::bindInput2D(const std::string& port, int h, int w, double gain, double epsilonFire, const std::vector<int>& attachLayers) {
    // create or reuse 2D edge
    int edgeIndex;
    auto edgeIt = inputEdges.find(port);
    if (edgeIt != inputEdges.end() && dynamic_cast<InputLayer2D*>(layers[edgeIt->second].get()) != nullptr) {
        edgeIndex = edgeIt->second;
    } else {
        edgeIndex = addInputLayer2D(h, w, gain, epsilonFire);
        inputEdges[port] = edgeIndex;
    }
    // wire edge -> attached layers
    for (int layerIndex : attachLayers) {
        connectLayers(edgeIndex, layerIndex, /*probability=*/1.0, /*feedback=*/false);
    }
}



void Region::bindOutput(const std::string& port, const std::vector<int>& layerIndices) {
    outputPorts[port] = layerIndices;
    int outEdge = ensureOutputEdge(port);
    for (int layerIndex : layerIndices) {
        connectLayers(layerIndex, outEdge, /*probability=*/1.0, /*feedback=*/false);
    }
}

// ---------------- pulses ----------------

void Region::pulseInhibition(double factor) {
    bus.setInhibitionFactor(factor);
    for (auto& layer : layers) {
        layer->getBus().setInhibitionFactor(factor);
    }
}

void Region::pulseModulation(double factor) {
    bus.setModulationFactor(factor);
    for (auto& layer : layers) {
        layer->getBus().setModulationFactor(factor);
    }
}

// ---------------- ticks ----------------

// Drive a scalar into the edge bound to `port` (edge-only delivery) and collect metrics.
RegionMetrics Region::tick(const std::string& port, double value) {
    RegionMetrics metrics;

    auto edgeIt = inputEdges.find(port);
    if (edgeIt == inputEdges.end()) {
        throw std::invalid_argument("No InputEdge for port '" + port + "'. Bind input first.");
    }

    int edgeIndex = edgeIt->second;
    layers[edgeIndex]->forward(value);
    metrics.incDeliveredEvents(1);

    for (auto& layer : layers) layer->endTick();
    bus.decay();

    for (auto& layer : layers) {
        for (auto& neuron : layer->getNeurons()) {
            metrics.addSlots(static_cast<long long>(neuron->getSlots().size()));
            metrics.addSynapses(static_cast<long long>(neuron->getOutgoing().size()));
        }
    }
    return metrics;
}


// Drive a 2D frame into an InputLayer2D edge bound to `port`.
RegionMetrics Region::tickImage(const std::string& port, const std::vector<std::vector<double>>& frame) {
    RegionMetrics metrics;

    auto edgeIt = inputEdges.find(port);
    if (edgeIt == inputEdges.end()) {
        throw std::invalid_argument("No InputEdge for port '" + port + "'. Bind a 2D input edge first.");
    }

    int edgeIndex = edgeIt->second;
    if (auto input2DLayer = dynamic_cast<InputLayer2D*>(layers[edgeIndex].get())) {
        input2DLayer->forwardImage(frame);
        metrics.incDeliveredEvents(1);
    } else {
        throw std::invalid_argument("InputEdge for '" + port + "' is not 2D (expected InputLayer2D).");
    }

    for (auto& layer : layers) layer->endTick();
    bus.decay();

    for (auto& layer : layers) {
        for (auto& neuron : layer->getNeurons()) {
            metrics.addSlots(static_cast<long long>(neuron->getSlots().size()));
            metrics.addSynapses(static_cast<long long>(neuron->getOutgoing().size()));
        }
    }
    return metrics;
}



int Region::addInputLayerND(const std::vector<int>& shape, double gain, double epsilonFire) {
    layers.push_back(std::make_shared<InputLayerND>(shape, gain, epsilonFire));
    return static_cast<int>(layers.size() - 1);
}

void Region::bindInputND(const std::string& port, const std::vector<int>& shape, double gain, double epsilonFire, const std::vector<int>& attachLayers) {
    int edgeIndex;
    auto edgeIt2 = inputEdges.find(port);
    if (edgeIt2 != inputEdges.end()) {
        auto maybeNd = dynamic_cast<InputLayerND*>(layers[edgeIt2->second].get());
        if (maybeNd != nullptr && maybeNd->hasShape(shape)) {
            edgeIndex = edgeIt2->second;
        } else {
            edgeIndex = addInputLayerND(shape, gain, epsilonFire);
            inputEdges[port] = edgeIndex;
        }
    } else {
        edgeIndex = addInputLayerND(shape, gain, epsilonFire);
        inputEdges[port] = edgeIndex;
    }
    for (int layerIndex : attachLayers) {
        connectLayers(edgeIndex, layerIndex, /*probability=*/1.0, /*feedback=*/false);
    }
}

// Drive a row-major flat tensor + shape into an InputLayerND edge bound to `port`.
RegionMetrics Region::tickND(const std::string& port, const std::vector<double>& flat, const std::vector<int>& shape) {
    RegionMetrics metrics;

    auto edgeIt3 = inputEdges.find(port);
    if (edgeIt3 == inputEdges.end()) {
        throw std::invalid_argument("No InputEdge for port '" + port + "'. Bind an ND input edge first.");
    }

    int edgeIndex = edgeIt3->second;
    auto inputNd = dynamic_cast<InputLayerND*>(layers[edgeIndex].get());
    if (!inputNd) {
        throw std::invalid_argument("InputEdge for '" + port + "' is not ND (expected InputLayerND).");
    }

    inputNd->forwardND(flat, shape);
    metrics.incDeliveredEvents(1);

    for (auto& layer : layers) layer->endTick();
    bus.decay();

    for (auto& layer : layers) {
        for (auto& neuron : layer->getNeurons()) {
            metrics.addSlots(static_cast<long long>(neuron->getSlots().size()));
            metrics.addSynapses(static_cast<long long>(neuron->getOutgoing().size()));
        }
    }
    return metrics;
}

} // namespace grownet
