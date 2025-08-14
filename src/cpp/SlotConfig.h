#pragma once
#include <vector>

namespace grownet {

enum class SlotPolicy { FIXED, NONUNIFORM, ADAPTIVE };

struct SlotConfig {
    SlotPolicy policy { SlotPolicy::FIXED };
    double slotWidthPercent { 10.0 };
    std::vector<double> nonuniformEdges; // ascending
    int maxSlots { -1 }; // -1 = unbounded

    static SlotConfig fixed(double widthPercent) {
        SlotConfig c; c.policy = SlotPolicy::FIXED; c.slotWidthPercent = widthPercent; return c;
    }
    static SlotConfig nonuniform(const std::vector<double>& edgesAsc) {
        SlotConfig c; c.policy = SlotPolicy::NONUNIFORM; c.nonuniformEdges = edgesAsc; return c;
    }
    static SlotConfig adaptive(double seedWidthPercent, int max) {
        SlotConfig c; c.policy = SlotPolicy::ADAPTIVE; c.slotWidthPercent = seedWidthPercent; c.maxSlots = max; return c;
    }
    static SlotConfig singleSlot() {
        return fixed(100.0);
    }
};

} // namespace grownet
