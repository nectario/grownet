#include <iostream>
#include <random>
#include "Region.h"

using namespace grownet;

int main() {
    Region region("vision");
    int l0 = region.addLayer(40, 8, 4);
    int l1 = region.addLayer(30, 6, 3);

    region.bindInput("pixels", {l0});
    region.connectLayers(l0, l1, 0.10, false);
    region.connectLayers(l1, l0, 0.01, true); // sparse feedback

    std::mt19937_64 rng(std::random_device{}());
    std::uniform_real_distribution<double> uni(0.0, 1.0);

    for (int step = 1; step <= 2000; ++step) {
        RegionMetrics m = region.tick("pixels", uni(rng));
        if (step % 200 == 0) {
            std::cout << "[step " << step << "] delivered=" << m.deliveredEvents
                      << " slots=" << m.totalSlots
                      << " syn="   << m.totalSynapses << "\n";
        }
    }

    PruneSummary p = region.prune();
    std::cout << "Prune summary: syn=" << p.prunedSynapses
              << " edges=" << p.prunedEdges << std::endl;
    return 0;
}
