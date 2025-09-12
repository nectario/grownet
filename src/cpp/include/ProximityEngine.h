#pragma once

namespace grownet {

struct ProximityConfig;
class Region;

struct ProximityEngine {
    // Apply proximity connectivity policy for the given region/config.
    // Returns number of edges added (best-effort; may return 0).
    static int Apply(Region& region, const ProximityConfig& cfg);

    // Contract-parity alias: prefer apply(...) in public API; keep Apply(...) for legacy callers.
    static inline int apply(Region& region, const ProximityConfig& cfg) {
        return Apply(region, cfg);
    }
};

} // namespace grownet
