#include <iostream>
#include "Region.h"

using namespace grownet;

int main_region_demo() {
    Region region("vision");
    int l0 = region.addLayer(40, 8, 4);
    int l1 = region.addLayer(30, 6, 3);
    region.bindInput("pixels", {l0});
    region.connectLayers(l0, l1, 0.1, false);
    region.connectLayers(l1, l0, 0.01, true);

    for (int step = 1; step <= 200; ++step) {
        auto m = region.tick("pixels", (double)step);
        if (step % 20 == 0) {
            std::cout << "[step " << step << "] delivered=" << m.deliveredEvents
                      << " slots=" << m.totalSlots << " syn=" << m.totalSynapses << "\n";
        }
    }
    auto ps = region.prune(10000, 0.05);
    std::cout << "Prune summary: prunedSynapses=" << ps.prunedSynapses << "\n";
    return 0;
}
