// File: src/cpp/include/ProximityConfig.h
#pragma once
#include <vector>
#include <cstdint>

struct ProximityConfig {
    bool   proximityConnectEnabled {false};
    double proximityRadius {1.0};
    enum class Function { STEP, LINEAR, LOGISTIC } proximityFunction {Function::STEP};
    double linearExponentGamma {1.0};
    double logisticSteepnessK {4.0};
    int    proximityMaxEdgesPerTick {128};
    int    proximityCooldownTicks {5};
    std::int64_t developmentWindowStart {0};
    std::int64_t developmentWindowEnd {INT64_MAX};
    int    stabilizationHits {3};
    bool   decayIfUnused {true};
    int    decayHalfLifeTicks {200};
    std::vector<int> candidateLayers {};  // empty -> all trainable layers
    bool   recordMeshRulesOnCrossLayer {true};
};
