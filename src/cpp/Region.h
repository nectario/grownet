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

namespace grownet {

/** Simple DTO with add/inc helpers to mirror Java semantics. */
struct RegionMetrics {
    long long deliveredEvents {0};
    long long totalSlots {0};
    long long totalSynapses {0};
    // legacy alias used by some demos
    long long delivered_events {0};

    // Optional spatial metrics (Phase B)
    long long activePixels {0};
    double centroidRow {0.0};
    double centroidCol {0.0};
    int bboxRowMin {0};
    int bboxRowMax {-1};
    int bboxColMin {0};
    int bboxColMax {-1};

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
    int addInputLayer2D(int h, int w, double gain, double epsilonFire);
    int addOutputLayer2D(int h, int w, double smoothing);

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
    RegionBus bus;
    bool enableSpatialMetrics { false };

    std::unordered_map<std::string, std::vector<int>> inputPorts;
    std::unordered_map<std::string, std::vector<int>> outputPorts;

    std::unordered_map<std::string, int> inputEdges;
    std::unordered_map<std::string, int> outputEdges;
};

} // namespace grownet
