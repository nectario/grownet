#pragma once
#include <functional>

namespace grownet {
    class Neuron;

    // Called when a neuron fires. Signature: (inputValue, self)
    using FireHook = std::function<void(double, Neuron&)>;
} // namespace grownet
