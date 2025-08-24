#pragma once
#include <memory>
#include <string>
#include <unordered_map>
#include <vector>
#include <stdexcept>

#include "RegionBus.h"
#include "Tract.h"
#include "Layer.h"
#include "Neuron.h"
#include "InputLayer2D.h"
#include "OutputLayer2D.h"

namespace grownet {

/** Simple DTO with add/inc helpers to mirror Java semantics. */
struct RegionMetrics {
    long long deliveredEvents {0};
    long long totalSlots {0};
    long long totalSynapses {0};
    // legacy alias used by some demos
    long long delivered_events {0};

    inline void incDeliveredEvents(long long by = 1) {
        deliveredEvents += by;
        delivered_events += by;
    }
    inline void addSlots(long long n) { totalSlots += n; }
    inline void addSynapses(long long n) { totalSynapses += n; }
};

/** Prune result (tract-level reserved). */
struct PruneSummary {
    long long prunedSynapses {0};
    long long prunedEdges {0};
};

/** Region orchestrates layers, tracts, ports, and pulses. */
class Region {
public:
    explicit Region(std::string name);

    int addLayer(int excitatoryCount, int inhibitoryCount, int modulatoryCount);
    int addInputLayer2D(int h, int w, double gain, double epsilonFire);
    int addOutputLayer2D(int h, int w, double smoothing);

    Tract& connectLayers(int sourceIndex, int destIndex, double probability, bool feedback=false);

    void bindInput(const std::string& port, const std::vector<int>& layerIndices);
    void bindInput2D(const std::string& port, int h, int w, double gain, double epsilonFire, const std::vector<int>& attachLayers);
    void bindOutput(const std::string& port, const std::vector<int>& layerIndices);

    void pulseInhibition(double factor);
    void pulseModulation(double factor);

    RegionMetrics tick(const std::string& port, double value);
    RegionMetrics tickImage(const std::string& port, const std::vector<std::vector<double>>& frame);

    const std::string& getName() const { return name; }
    std::vector<std::shared_ptr<Layer>>& getLayers() { return layers; }
    std::vector<std::unique_ptr<Tract>>& getTracts() { return tracts; }
    RegionBus& getBus() { return bus; }

private:
    // Create one-neuron edge layers lazily per port
    int ensureInputEdge(const std::string& port);
    int ensureOutputEdge(const std::string& port);

private:
    std::string name;
    std::vector<std::shared_ptr<Layer>> layers;      // shared_ptr keeps addresses stable
    std::vector<std::unique_ptr<Tract>> tracts;
    RegionBus bus;

    std::unordered_map<std::string, std::vector<int>> inputPorts;
    std::unordered_map<std::string, std::vector<int>> outputPorts;

    std::unordered_map<std::string, int> inputEdges;
    std::unordered_map<std::string, int> outputEdges;
};

} // namespace grownet
