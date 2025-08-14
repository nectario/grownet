#pragma once
#include <optional>
#include <vector>

namespace grownet {

enum class SlotPolicy { Fixed, NonUniform, Adaptive };

struct SlotConfig {
    SlotPolicy policy { SlotPolicy::Fixed };
    double slotWidthPercent { 10.0 };               // used by Fixed & Adaptive
    std::vector<double> nonuniformEdges {};         // ascending percent edges
    std::optional<int> maxSlots {};                 // std::nullopt => unbounded
};

} // namespace grownet
