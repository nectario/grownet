// File: src/cpp/src/ProximityEngine.cpp
// NOTE: ADAPT Region API types and calls to your codebase.
#include "ProximityConfig.h"
#include "DeterministicLayout.h"
#include "SpatialHash.h"
#include <tuple>
#include <cmath>
#include <stdexcept>

namespace ProximityEngine {

    struct RegionState {
        // Map key: "layer:neuron" -> last attempt step
        std::unordered_map<std::string, long long> lastAttemptByNeuron;
    };

    static std::unordered_map<void*, RegionState> stateByRegion;

    static std::string makeNeuronKey(int layerIndex, int neuronIndex) {
        return std::to_string(layerIndex) + ":" + std::to_string(neuronIndex);
    }

    static double probabilityFromDistance(double distance, const ProximityConfig& cfg) {
        if (cfg.proximityFunction == ProximityConfig::Function::STEP) {
            return (distance <= cfg.proximityRadius) ? 1.0 : 0.0;
        }
        double unit = std::max(0.0, 1.0 - distance / std::max(cfg.proximityRadius, 1e-12));
        if (cfg.proximityFunction == ProximityConfig::Function::LINEAR) {
            return std::pow(unit, std::max(cfg.linearExponentGamma, 1e-12));
        }
        return 1.0 / (1.0 + std::exp(cfg.logisticSteepnessK * (distance - cfg.proximityRadius)));
    }

    template <typename Region>
    int Apply(Region& region, const ProximityConfig& cfg) {
        if (!cfg.proximityConnectEnabled) return 0;
        long long currentStep = region.bus().get_current_step(); // ADAPT accessor
        if (currentStep < cfg.developmentWindowStart || currentStep > cfg.developmentWindowEnd) return 0;

        RegionState& state = stateByRegion[static_cast<void*>(&region)]; // keyed by address
        std::vector<int> candidateLayers = cfg.candidateLayers.empty()
            ? std::vector<int>(region.layerCount()) // ADAPT: construct 0..N-1
            : cfg.candidateLayers;

        if (cfg.candidateLayers.empty()) {
            for (int layerIndex = 0; layerIndex < region.layerCount(); ++layerIndex) candidateLayers[layerIndex] = layerIndex;
        }

        SpatialHash<std::pair<int,int>> grid(cfg.proximityRadius);

        for (int layerIndex : candidateLayers) {
            auto& layer = region.layer(layerIndex); // ADAPT
            int layerHeight = layer.getHeight();    // ADAPT
            int layerWidth  = layer.getWidth();     // ADAPT
            int neuronCount = layer.getNeuronCount(); // ADAPT
            for (int neuronIndex = 0; neuronIndex < neuronCount; ++neuronIndex) {
                auto pos = DeterministicLayout::position("region", layerIndex, neuronIndex, layerHeight, layerWidth);
                grid.insert({layerIndex, neuronIndex}, pos);
            }
        }

        // Require region RNG for probabilistic modes (STEP works without RNG).
        bool probabilistic = (cfg.proximityFunction != ProximityConfig::Function::STEP);
        auto* rng = probabilistic ? region.rng() : nullptr; // ADAPT
        if (probabilistic && rng == nullptr) {
            throw std::runtime_error("ProximityEngine: probabilistic mode requires a seeded region RNG");
        }

        int edgesAdded = 0;

        for (int layerIndex : candidateLayers) {
            auto& layer = region.layer(layerIndex);
            int layerHeight = layer.getHeight();
            int layerWidth  = layer.getWidth();
            int neuronCount = layer.getNeuronCount();
            for (int neuronIndex = 0; neuronIndex < neuronCount; ++neuronIndex) {
                std::string neuronKey = makeNeuronKey(layerIndex, neuronIndex);
                long long lastAttempt = (state.lastAttemptByNeuron.count(neuronKey) ? state.lastAttemptByNeuron[neuronKey] : LLONG_MIN);
                if ((currentStep - lastAttempt) < cfg.proximityCooldownTicks) continue;

                auto origin = DeterministicLayout::position("region", layerIndex, neuronIndex, layerHeight, layerWidth);
                auto candidates = grid.near(origin);
                for (const auto& neighbor : candidates) {
                    int neighborLayerIndex = neighbor.first;
                    int neighborNeuronIndex = neighbor.second;
                    if (neighborLayerIndex == layerIndex && neighborNeuronIndex == neuronIndex) continue;
                    if (region.hasEdge(layerIndex, neuronIndex, neighborLayerIndex, neighborNeuronIndex)) continue; // ADAPT canonical

                    auto nhLayer = region.layer(neighborLayerIndex);
                    int nh = nhLayer.getHeight();
                    int nw = nhLayer.getWidth();
                    auto neighborPos = DeterministicLayout::position("region", neighborLayerIndex, neighborNeuronIndex, nh, nw);
                    double dx = std::get<0>(origin) - std::get<0>(neighborPos);
                    double dy = std::get<1>(origin) - std::get<1>(neighborPos);
                    double dz = std::get<2>(origin) - std::get<2>(neighborPos);
                    double distance = std::sqrt(dx*dx + dy*dy + dz*dz);
                    if (distance > cfg.proximityRadius) continue;

                    double probability = probabilityFromDistance(distance, cfg);
                    bool accept = (probability >= 1.0) || (probabilistic && rng->uniform() < probability); // ADAPT rng
                    if (!accept) continue;

                    region.connectNeurons(layerIndex, neuronIndex, neighborLayerIndex, neighborNeuronIndex, /*feedback=*/false); // ADAPT method
                    if (cfg.recordMeshRulesOnCrossLayer && layerIndex != neighborLayerIndex) {
                        region.recordMeshRuleFor(layerIndex, neighborLayerIndex, 1.0, false); // ADAPT
                    }

                    state.lastAttemptByNeuron[neuronKey] = currentStep;
                    state.lastAttemptByNeuron[makeNeuronKey(neighborLayerIndex, neighborNeuronIndex)] = currentStep;

                    edgesAdded += 1;
                    if (edgesAdded >= cfg.proximityMaxEdgesPerTick) return edgesAdded;
                }
            }
        }
        return edgesAdded;
    }
} // namespace ProximityEngine
