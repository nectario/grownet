#pragma once
#include <vector>
#include <algorithm>

namespace grownet {

struct SlotPolicyConfig {
    enum Mode { FIXED, MULTI_RESOLUTION, ADAPTIVE };
    Mode mode = FIXED;

    double slotWidthPercent = 0.10;                 // used for FIXED and as starting point for ADAPTIVE
    std::vector<double> multiresWidths {0.10, 0.05, 0.02}; // coarse -> fine
    int boundaryRefineHits = 5;

    int targetActiveLow  = 6;                       // adaptive: desired range for active slots per neuron
    int targetActiveHigh = 12;
    double minSlotWidth = 0.01;                     // clamp adaptive width
    double maxSlotWidth = 0.20;
    int adjustCooldownTicks = 200;                  // adaptive: only adjust every N ticks
    double adjustFactorUp   = 1.2;                  // widen
    double adjustFactorDown = 0.9;                  // narrow

    std::vector<double> nonuniformSchedule;         // optional per-new-slot widths; empty = off
};

} // namespace grownet
