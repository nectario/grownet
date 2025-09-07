// Optional proximity connectivity engine (sidecar). Not integrated by default.
#include "DeterministicLayout.h"
#include "SpatialHash.h"
#include "ProximityConfig.h"
#include "Region.h"

namespace grownet {

static inline double euclidean(double ax, double ay, double az, double bx, double by, double bz) {
    const double dx = ax - bx; const double dy = ay - by; const double dz = az - bz;
    return std::sqrt(dx*dx + dy*dy + dz*dz);
}

struct ProximityEngine {
    // Apply proximity policy. Returns added edge count.
    static int Apply(Region& /*region*/, const ProximityConfig& /*cfg*/) {
        // Intentionally left unintegrated to avoid altering core Region tick.
        // Provide a future hook to call this from Region when enabled.
        return 0;
    }
};

} // namespace grownet

