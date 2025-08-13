
#include <iostream>
#include "Region.h"

using namespace grownet;

int main() {
    Region region("vision");

    int l0 = region.addLayer(8, 2, 1);
    int l1 = region.addLayer(12, 3, 2);

    region.connectLayers(l0, l1, 0.2, false);
    region.bindInput("pixels", {l0});

    for (int t = 0; t < 100; ++t) {
        double value = (t % 10) * 0.1; // simple varying input
        RegionMetrics m = region.tick("pixels", value);
        if (t % 10 == 0) {
            std::cout << "[t=" << t << "] delivered=" << m.deliveredEvents
                      << " slots=" << m.totalSlots
                      << " synapses=" << m.totalSynapses << std::endl;
        }
    }

    PruneSummary ps = region.prune();
    std::cout << "Pruned synapses: " << ps.prunedSynapses
              << " | pruned edges: " << ps.prunedEdges << std::endl;
    return 0;
}
