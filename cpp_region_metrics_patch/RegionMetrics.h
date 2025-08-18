// File: src/cpp/RegionMetrics.h
// Standalone metrics container (mirrors Java ai.nektron.grownet.metrics.RegionMetrics).
// Move of fields from Region::Metrics -> RegionMetrics with private members and mutators.

#pragma once
#include <cstddef>

namespace grownet {

class RegionMetrics {
    long long deliveredEvents_ = 0;
    long long totalSlots_ = 0;
    long long totalSynapses_ = 0;

public:
    RegionMetrics() = default;

    // --- getters ---
    inline long long getDeliveredEvents() const { return deliveredEvents_; }
    inline long long getTotalSlots() const { return totalSlots_; }
    inline long long getTotalSynapses() const { return totalSynapses_; }

    // --- mutators/accumulators ---
    inline void incDeliveredEvents(long long delta = 1) { deliveredEvents_ += delta; }
    inline void addSlots(long long n) { totalSlots_ += n; }
    inline void addSynapses(long long n) { totalSynapses_ += n; }
};

} // namespace grownet
