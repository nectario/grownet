// src/cpp/tests/region_tick_tests.cpp
#include <cassert>
#include <iostream>
#include <vector>
#include "Region.h"

using namespace grownet;

static void testSingleTickNoTracts() {
    Region region("t");
    int inputLayer = region.addLayer(1,0,0);
    region.bindInput("x", std::vector<int>{inputLayer});
    RegionMetrics m = region.tick("x", 0.42);
    std::cout << "[C++] singleTickNoTracts delivered=" << m.deliveredEvents
              << " slots=" << m.totalSlots << " syn=" << m.totalSynapses << std::endl;
    assert(m.deliveredEvents == 1);
    assert(m.totalSlots >= 1);
    assert(m.totalSynapses >= 0);
}

static void testConnectLayersFullMesh() {
    Region region("t");
    int src = region.addLayer(2,0,0);
    int dst = region.addLayer(3,0,0);
    // We only need the side effect (subscriptions); ignore the return ref.
    (void)region.connectLayers(src, dst, 1.0, false);
    // Aggregate structure via a tick (port may be unbound; still aggregates structure)
    RegionMetrics m = region.tick("x", 0.0);
    std::cout << "[C++] connectLayersFullMesh totalSynapses=" << m.totalSynapses << std::endl;
    assert(m.totalSynapses >= 2*3);
}

static void testImageInputEventCount() {
    Region region("t");
    int inIdx = region.addInputLayer2D(2,2,1.0,0.01);
    region.bindInput("pixels", std::vector<int>{inIdx});
    std::vector<std::vector<double>> frame{{0.0,1.0},{0.0,0.0}};
    RegionMetrics m = region.tickImage("pixels", frame);
    std::cout << "[C++] imageInputEventCount delivered=" << m.deliveredEvents << std::endl;
    assert(m.deliveredEvents == 1);
}

#ifndef GTEST_AVAILABLE
int main() {
    testSingleTickNoTracts();
    testConnectLayersFullMesh();
    testImageInputEventCount();
    std::cout << "[C++] All RegionTick tests passed." << std::endl;
    return 0;
}
#endif
