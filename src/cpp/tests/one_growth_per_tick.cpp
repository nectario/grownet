#ifdef GTEST_AVAILABLE
#include <gtest/gtest.h>
#endif

#include "Region.h"

#ifdef GTEST_AVAILABLE
TEST(RegionGrowth, AtMostOnePerTick) {
    grownet::Region region("one-per-tick");
    int in = region.addInputLayer2D(4,4,1.0,0.01);
    int hid = region.addLayer(6,0,0);
    region.connectLayersWindowed(in, hid, 2,2,1,1, std::string("valid"), false);
    region.bindInput2D("img", {4,4}, 1.0, 0.01, {in});

    grownet::GrowthPolicy policy;
    policy.enableRegionGrowth = true;
    policy.maximumLayers = 64;
    policy.averageSlotsThreshold = 0.0;
    policy.layerCooldownTicks = 0;
    region.setGrowthPolicy(policy);

    int prevLayers = static_cast<int>(region.getLayers().size());
    for (int t = 0; t < 5; ++t) {
        region.tick2D("img", std::vector<std::vector<double>>(4, std::vector<double>(4, 1.0)));
        int nowLayers = static_cast<int>(region.getLayers().size());
        int delta = nowLayers - prevLayers;
        EXPECT_TRUE(delta == 0 || delta == 1);
        prevLayers = nowLayers;
    }
}
#endif

