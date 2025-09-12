/**
 * @file Region.h
 * @brief Region orchestrates layers, port bindings, and edge-only ticks.
 *
 * Ports are modeled as edge layers (scalar or shape-aware). A tick drives the
 * bound edge exactly once; downstream layers receive activity via wiring from
 * that edge. Metrics mirror the Java reference via RegionMetrics helpers.
 */
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
#include "InputLayerND.h"
#include "GrowthPolicy.h"
#include "ProximityConfig.h"
#include "TractWindowed.h"

namespace grownet {

/** Simple DTO with add/inc helpers to mirror Java semantics. */
struct RegionMetrics {
    long long deliveredEvents {0};
    long long totalSlots {0};
    long long totalSynapses {0};

    // Optional spatial metrics (Phase B)
    long long activePixels {0};
    double centroidRow {0.0};
    double centroidCol {0.0};
    int bboxRowMin {0};
    int bboxRowMax {-1};
    int bboxColMin {0};
    int bboxColMax {-1};

    inline void incDeliveredEvents(long long by = 1) { deliveredEvents += by; }
    inline void addSlots(long long n) { totalSlots += n; }
    inline void addSynapses(long long n) { totalSynapses += n; }

    // Read accessors (parity with Java getters)
    inline long long getDeliveredEvents() const { return deliveredEvents; }
    inline long long getTotalSlots() const { return totalSlots; }
    inline long long getTotalSynapses() const { return totalSynapses; }
    inline long long getActivePixels() const { return activePixels; }
    inline int getBboxRowMin() const { return bboxRowMin; }
    inline int getBboxRowMax() const { return bboxRowMax; }
    inline int getBboxColMin() const { return bboxColMin; }
    inline int getBboxColMax() const { return bboxColMax; }
    inline double getCentroidRow() const { return centroidRow; }
    inline double getCentroidCol() const { return centroidCol; }
};

// Minimal summary for prune operations (currently a no-op).
struct PruneSummary {
    long long prunedSynapses {0};
    long long prunedEdges {0};
};

/**
 * @brief Group of layers with helpers for wiring and ticking.
 *
 * - Ports-as-edges: bindInput/bindInput2D/bindInputND create edges lazily.
 * - Ticks: edge-only delivery (`tick`, `tickImage`, `tickND`), then end-of-tick
 *   housekeeping and structural metric aggregation.
 * - Safety: throws std::out_of_range/invalid_argument for invalid indices/ports.
 */
class Region {
public:
    explicit Region(std::string name);

    int addLayer(int excitatoryCount, int inhibitoryCount, int modulatoryCount);

    Tract& connectLayers(int sourceIndex, int destIndex, double probability, bool feedback=false);
    // Windowed deterministic wiring (spatial focus helper).
    // Return value: number of UNIQUE source subscriptions (i.e., the count of
    // distinct source pixels that participate in ≥1 window). It is NOT the raw
    // number of (src,dst) edges created.
    int connectLayersWindowed(int sourceIndex, int destIndex,
                              int kernelH, int kernelW,
                              int strideH=1, int strideW=1,
                              const std::string& padding="valid",
                              bool feedback=false);

    void bindInput(const std::string& port, const std::vector<int>& layerIndices);
    void bindInput2D(const std::string& port, int height, int width, double gain, double epsilonFire, const std::vector<int>& attachLayers);
    // Convenience overload: pass shape as {H,W}
    void bindInput2D(const std::string& port, const std::vector<int>& shape, double gain, double epsilonFire, const std::vector<int>& attachLayers);
    int addInputLayer2D(int height, int width, double gain, double epsilonFire);
    // Convenience alias used by some tests/demos
    int addInput2DLayer(int height, int width) { return addInputLayer2D(height, width, 1.0, 0.01); }
    int addOutputLayer2D(int height, int width, double smoothing);
    void bindOutput(const std::string& port, const std::vector<int>& layerIndices);

    void pulseInhibition(double factor);
    void pulseModulation(double factor);

    RegionMetrics tick(const std::string& port, double value);
    RegionMetrics tick2D(const std::string& port, const std::vector<std::vector<double>>& frame);
    RegionMetrics tickImage(const std::string& port, const std::vector<std::vector<double>>& frame);
    RegionMetrics computeSpatialMetrics(const std::vector<std::vector<double>>& image2d, bool preferOutput);

    // --- No-op prune stubs to keep demos/tests compiling ---
    PruneSummary prune(long long synapseStaleWindow, double synapseMinStrength);
    PruneSummary prune(long long synapseStaleWindow, double synapseMinStrength,
                       long long tractStaleWindow,  double tractMinStrength);

    const std::string& getName() const { return name; }
    std::vector<std::shared_ptr<Layer>>& getLayers() { return layers; }
    std::vector<std::unique_ptr<Tract>>& getTracts() { return tracts; }
    RegionBus& getBus() { return bus; }



public:
    // N-D input support (row-major)
    int addInputLayerND(const std::vector<int>& shape, double gain, double epsilonFire);
    void bindInputND(const std::string& port, const std::vector<int>& shape, double gain, double epsilonFire, const std::vector<int>& attachLayers);
    RegionMetrics tickND(const std::string& port, const std::vector<double>& flat, const std::vector<int>& shape);
private:
    // Create one-neuron edge layers lazily per port
    int ensureInputEdge(const std::string& port);
    int ensureOutputEdge(const std::string& port);

private:
    std::string name;
    std::vector<std::shared_ptr<Layer>> layers;      // shared_ptr keeps addresses stable
    std::vector<std::unique_ptr<Tract>> tracts;
    std::vector<std::unique_ptr<TractWindowed>> windowedTracts; // recorded geometry for windowed wiring
    RegionBus bus;
    bool enableSpatialMetrics { false };
    struct MeshRule { int src; int dst; double prob; bool feedback; };
    std::vector<MeshRule> meshRules;
    std::mt19937 rng { 1234 };

    std::unordered_map<std::string, std::vector<int>> inputPorts;
    std::unordered_map<std::string, std::vector<int>> outputPorts;

    std::unordered_map<std::string, int> inputEdges;
    std::unordered_map<std::string, int> outputEdges;
public:
    // Growth auto-wiring helpers
    void autowireNewNeuron(Layer* sourceLayerPtr, int newNeuronIndex);
    int requestLayerGrowth(Layer* saturated);
    int requestLayerGrowth(Layer* saturated, double connectionProbability);

    // Region growth policy (layers → region)
    void setGrowthPolicy(const GrowthPolicy& policy) { growthPolicy = policy; hasGrowthPolicy = true; }
    const GrowthPolicy* getGrowthPolicy() const { return hasGrowthPolicy ? &growthPolicy : nullptr; }
    void maybeGrowRegion();

    // Proximity policy helpers
    void setProximityConfig(const ProximityConfig& cfg) { proximityConfig = cfg; hasProximityConfig = true; }
    const ProximityConfig* getProximityConfig() const { return hasProximityConfig ? &proximityConfig : nullptr; }

private:
    GrowthPolicy growthPolicy{};
    bool hasGrowthPolicy { false };
    long long lastRegionGrowthStep { -1 };
    ProximityConfig proximityConfig{};
    bool hasProximityConfig { false };
    long long lastProximityTickStep { -1 };
};

} // namespace grownet
    void bindInput2D(const std::string& port, int height, int width, double gain, double epsilonFire, const std::vector<int>& attachLayers);
