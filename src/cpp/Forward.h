#pragma once
#include <functional>
#include <memory>
#include <unordered_map>
#include <vector>
#include <string>

namespace grownet {
    class Neuron;
    class Layer;
    class Tract;
    class LateralBus;
    class RegionBus;
    struct SlotConfig;
    struct Weight;
    using FireHook = std::function<void(Neuron*, double)>;
}
