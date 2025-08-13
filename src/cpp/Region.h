
#pragma once
#include <memory>
#include <string>
#include <unordered_map>
#include <vector>

#include "RegionBus.h"
#include "Tract.h"
#include "Layer.h"
#include "Neuron.h"

namespace grownet {

struct RegionMetrics {
    int deliveredEvents {0};
    int totalSlots      {0};
    int totalSynapses   {0};
};

struct PruneSummary {
    int prunedSynapses {0};
    int prunedEdges    {0};
};

class Region {
public:
    explicit Region(std::string regionName);

    int addLayer(int excitatoryCount, int inhibitoryCount, int modulatoryCount);
    Tract& connectLayers(int sourceIndex, int destIndex, double probability, bool feedback = false);
    void bindInput(const std::string& port, const std::vector<int>& layerIndices);
    void bindOutput(const std::string& port, const std::vector<int>& layerIndices);

    void pulseInhibition(double factor) { bus.setInhibitionFactor(factor); }
    void pulseModulation(double factor) { bus.setModulationFactor(factor); }

    RegionMetrics tick(const std::string& port, double value);

    PruneSummary prune(std::int64_t synapseStaleWindow = 10000, double synapseMinStrength = 0.05,
                       std::int64_t tractStaleWindow   = 10000, double tractMinStrength   = 0.05);

    const std::string& getName() const { return name; }
    std::vector<std::shared_ptr<Layer>>& getLayers() { return layers; }
    std::vector<std::unique_ptr<Tract>>& getTracts() { return tracts; }
    RegionBus& getBus() { return bus; }

private:
    std::string name;
    std::vector<std::shared_ptr<Layer>> layers;
    std::vector<std::unique_ptr<Tract>> tracts;
    RegionBus bus;
    std::unordered_map<std::string, std::vector<int>> inputPorts;
    std::unordered_map<std::string, std::vector<int>> outputPorts;
};

} // namespace grownet
