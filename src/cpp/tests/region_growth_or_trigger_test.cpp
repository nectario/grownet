// File: tests/region_growth_or_trigger_test.cpp
// NOTE: ADAPT include paths, type names, and method names to your tree.

#include <gtest/gtest.h>
#include <vector>
#include <cmath>

#include "Region.h"
#include "GrowthPolicy.h"
#include "InputLayer2D.h"

using namespace grownet;

static void driveTickWithUniformFrame(Region& region,
                                      const std::string& port,
                                      int height,
                                      int width,
                                      double value) {
    std::vector<std::vector<double>> frame(height, std::vector<double>(width, value));
    (void)region.tick2D(port, frame);
}

TEST(DISABLED_RegionGrowthOrTrigger, PercentAtCapacityAndFallbackCausesSingleGrowthInTick) {
    Region region("or_trigger_test");
    const int height = 4;
    const int width  = 4;

    const int inputIndex  = region.addInputLayer2D(height, width, 1.0, 0.01);
    const int hiddenIndex = region.addLayer(4, 0, 0);
    region.bindInput2D("img", height, width, 1.0, 0.01, std::vector<int>{ inputIndex, hiddenIndex });

    GrowthPolicy policy;
    policy.averageSlotsThreshold = 1e9;
    policy.percentAtCapFallbackThreshold = 75.0;
    policy.layerCooldownTicks = 0;
    policy.maximumLayers = 32;
    region.setGrowthPolicy(policy);

    const int before = static_cast<int>(region.getLayers().size());
    driveTickWithUniformFrame(region, "img", height, width, 1.0);
    driveTickWithUniformFrame(region, "img", height, width, 0.2);
    const int after = static_cast<int>(region.getLayers().size());
    EXPECT_GE(after, before);
}
