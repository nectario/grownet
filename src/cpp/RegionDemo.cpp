#include <iostream>
#include "Region.h"

int main_region_demo() {
    grownet::Region region("region_demo");
    int sourceLayerIndex = region.addLayer(8, 2, 1);
    int destLayerIndex = region.addLayer(8, 2, 1);
    region.bindInput("in", { sourceLayerIndex });
    region.connectLayers(sourceLayerIndex, destLayerIndex, 0.4, false);

    for (int tickIndex = 0; tickIndex < 5; ++tickIndex) {
        auto metrics = region.tick("in", (tickIndex % 2 == 0) ? 1.0 : 0.0);
        std::cout << "[t=" << tickIndex << "] delivered=" << metrics.deliveredEvents << "\n";
    }
    // NOTE: Region::prune(...) is not available in this build; skipping in demo.
    // auto pruneSummary = region.prune(10000, 0.05);
    // std::cout << "pruned synapses=" << pruneSummary.prunedSynapses << "\n";
    return 0;
}
