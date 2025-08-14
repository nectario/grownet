#include <iostream>
#include "Region.h"

int main_region_demo() {
    grownet::Region region("region_demo");
    int src = region.addLayer(8, 2, 1);
    int dst = region.addLayer(8, 2, 1);
    region.bindInput("in", { src });
    region.connectLayers(src, dst, 0.4, false);

    for (int t = 0; t < 5; ++t) {
        auto m = region.tick("in", (t % 2 == 0) ? 1.0 : 0.0);
        std::cout << "[t=" << t << "] delivered=" << m.deliveredEvents << "\n";
    }
    auto ps = region.prune(10000, 0.05);
    std::cout << "pruned synapses=" << ps.prunedSynapses << "\n";
    return 0;
}
