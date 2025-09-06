#include "Region.h"
#include <iostream>
#include <vector>

using namespace grownet;

int main() {
    const int height = 8;
    const int width  = 8;

    Region region("two-d-tick-demo");

    int inputIndex  = region.addInputLayer2D(height, width, /*gain=*/1.0, /*epsilonFire=*/0.01);
    int outputIndex = region.addOutputLayer2D(height, width, /*smoothing=*/0.0);

    int uniqueSources = region.connectLayersWindowed(
        inputIndex, outputIndex,
        /*kernelH*/3, /*kernelW*/3,
        /*strideH*/1, /*strideW*/1,
        /*padding*/"same",
        /*feedback*/false);
    std::cout << "unique_sources=" << uniqueSources << "\n";

    // Bind input port to the 2D edge and wire to the pipeline
    region.bindInput2D("pixels", height, width, 1.0, 0.01, std::vector<int>{ inputIndex });

    // Build an 8x8 frame and light a single pixel
    std::vector<std::vector<double>> frame(height, std::vector<double>(width, 0.0));
    frame[3][4] = 1.0;

    auto m1 = region.tick2D("pixels", frame);
    std::cout << "tick#1 delivered=" << m1.delivered_events
              << " slots=" << m1.total_slots
              << " synapses=" << m1.total_synapses << "\n";

    frame[3][4] = 0.0;
    frame[5][6] = 1.0;
    auto m2 = region.tick2D("pixels", frame);
    std::cout << "tick#2 delivered=" << m2.delivered_events
              << " slots=" << m2.total_slots
              << " synapses=" << m2.total_synapses << "\n";

    return 0;
}

