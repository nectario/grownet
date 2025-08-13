
#pragma once
#include <functional>

namespace grownet {
    class Neuron; // forward declaration

    using FireHook = std::function<void(double /*inputValue*/, const Neuron& /*self*/)>;
}
