// src/cpp/tests/region_pulse_and_binding_tests.cpp
#include <cassert>
#include <cmath>
#include <iostream>
#include <vector>
#include "Region.h"
#include "Layer.h"
#include "LateralBus.h"

using namespace grownet;

static void testMultiLayerInputBinding() {
    Region region("t");
    int l0 = region.addLayer(1,0,0);
    int l1 = region.addLayer(1,0,0);
    region.bindInput("x", std::vector<int>{l0, l1});
    RegionMetrics m = region.tick("x", 1.0);
    std::cout << "[C++] multiLayerBinding delivered=" << m.deliveredEvents << std::endl;
    assert(m.deliveredEvents == 2);
}

static void testPulseChecks() {
    Region region("t");
    int l0 = region.addLayer(1,0,0);
    region.bindInput("x", std::vector<int>{l0});

    // Access bus and set factors (simulating pulses)
    auto layers = region.getLayers();
    auto bus = layers[l0]->getBus();
    bus.setModulationFactor(1.5);
    bus.setInhibitionFactor(0.7);

    RegionMetrics m = region.tick("x", 0.5);
    // Silence -Wunused-but-set-variable in this smoke test.
    (void)m;
    std::cout << "[C++] pulseChecks post(mod=" << bus.getModulationFactor()
              << ", inh=" << bus.getInhibitionFactor() << ")" << std::endl;

    // C++ bus decay: inh *= 0.9; mod = 1.0
    assert(std::abs(bus.getModulationFactor() - 1.0) < 1e-12);
    assert(std::abs(bus.getInhibitionFactor() - 0.7 * 0.9) < 1e-9);
}

#ifndef GTEST_AVAILABLE
int main() {
    testMultiLayerInputBinding();
    testPulseChecks();
    std::cout << "[C++] RegionPulseAndBindingTests passed." << std::endl;
    return 0;
}
#endif
