#include <iostream>
#include <random>
#include <vector>
#include "Region.h"

using namespace grownet;

int main() {
    Region region("vision");
    int inputLayerIndex  = region.addLayer(40, 8, 4);
    int hiddenLayerIndex = region.addLayer(30, 6, 3);

    region.bindInput("pixels", std::vector<int>{inputLayerIndex});

    // Feedforward + tiny feedback trickle
    region.connectLayers(inputLayerIndex, hiddenLayerIndex, 0.10, false);
    region.connectLayers(hiddenLayerIndex, inputLayerIndex, 0.01, true);

    std::mt19937 rng(1234);
    std::uniform_real_distribution<double> uniform01(0.0, 1.0);

    for (int step = 1; step <= 500; ++step) {
        double value = uniform01(rng);
        RegionMetrics metrics = region.tick("pixels", value);  // per Region.h
        if (step % 100 == 0) {
            std::cout << "[step " << step << "] delivered=" << metrics.getDeliveredEvents()
                      << " slots=" << metrics.getTotalSlots()
                      << " syn=" << metrics.getTotalSynapses() << std::endl;
        }
    }

    PruneSummary summary = region.prune(10'000, 0.05, 10'000, 0.05);
    std::cout << "Prune summary: prunedSynapses=" << summary.prunedSynapses
              << " prunedEdges=" << summary.prunedEdges << std::endl;
    return 0;
}
