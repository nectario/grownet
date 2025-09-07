// Optional proximity connectivity policy configuration (sidecar module).
#pragma once
#include <set>

namespace grownet {

struct ProximityConfig {
    bool   proximityConnectEnabled { false };
    double proximityRadius { 1.0 };
    enum class Function { STEP, LINEAR, LOGISTIC };
    Function proximityFunction { Function::STEP };
    double linearExponentGamma { 1.0 };
    double logisticSteepnessK  { 4.0 };
    int    proximityMaxEdgesPerTick { 128 };
    int    proximityCooldownTicks   { 5 };
    long long developmentWindowStart { 0 };
    long long developmentWindowEnd   { (long long)0x7fffffffffffffffLL };
    int    stabilizationHits { 3 };
    bool   decayIfUnused { true };
    int    decayHalfLifeTicks { 200 };
    std::set<int> candidateLayers; // empty -> all layers
    bool   recordMeshRulesOnCrossLayer { true };
};

} // namespace grownet

