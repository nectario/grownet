#pragma once
#include <memory>
#include <string>
#include <unordered_map>
#include <vector>

#include "RegionBus.h"
#include "Tract.h"
#include "Layer.h"
#include "Neuron.h"
#include "InputLayer2D.h"
#include "OutputLayer2D.h"

namespace grownet {

    struct RegionMetrics {
        int deliveredEvents {0};
        int delivered_events {0}; // legacy alias for demos
        int totalSlots      {0};
        int totalSynapses   {0};
    };

    struct PruneSummary {
        int prunedSynapses {0};
        int prunedEdges    {0};
    };

    class Region {
    public:
        explicit Region(std::string name);

        // Construction
        int addLayer(int excitatoryCount, int inhibitoryCount, int modulatoryCount);
        int addInputLayer2D(int h, int w, double gain, double epsilonFire);
        int addOutputLayer2D(int h, int w, double smoothing);
        Tract& connectLayers(int sourceIndex, int destIndex, double probability, bool feedback = false);
        void bindInput(const std::string& port, const std::vector<int>& layerIndices);
        void bindOutput(const std::string& port, const std::vector<int>& layerIndices);

        // Region-wide pulses (one tick)
        void pulseInhibition(double factor) { bus.setInhibitionFactor(factor); }
        void pulseModulation(double factor) { bus.setModulationFactor(factor); }

        // Main loop (two-phase)
        RegionMetrics tick(const std::string& port, double value);
        RegionMetrics tickImage(const std::string& port, const std::vector<std::vector<double>>& frame);

        // Maintenance
        PruneSummary prune(long long /*synapseStaleWindow*/ = 10'000, double /*synapseMinStrength*/ = 0.05,
                           long long /*tractStaleWindow*/   = 10'000, double /*tractMinStrength*/   = 0.05) {
            // placeholder: no-op for now
            return PruneSummary{};
        }

        // Accessors
        const std::string& getName() const { return name; }
        std::vector<std::shared_ptr<Layer>>& getLayers() { return layers; }
        std::vector<std::unique_ptr<Tract>>& getTracts() { return tracts; }
        RegionBus& getBus() { return bus; }

    private:
        std::string name;
        std::vector<std::shared_ptr<Layer>> layers;      // shared_ptr keeps addresses stable
        std::vector<std::unique_ptr<Tract>> tracts;
        RegionBus bus;
        std::unordered_map<std::string, std::vector<int>> inputPorts;
        std::unordered_map<std::string, std::vector<int>> outputPorts;
    };

} // namespace grownet
